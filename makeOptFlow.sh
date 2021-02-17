#!/bin/bash

if [ ! -f ./consistencyChecker/consistencyChecker ]; then
  if [ ! -f ./consistencyChecker/Makefile ]; then
    echo "Consistency checker makefile not found."
    exit 1
  fi
  cd consistencyChecker/
  make
  cd ..
fi

workdir=$1
framesdir=$2
filePattern=$3
folderName=$4
flownet2Nvidia=$5
condaEnv=$6
startFrame=${7:-1}
stepSize=${8:-1}

source ~/anaconda3/etc/profile.d/conda.sh
conda activate ${condaEnv}

mkdir -p "${folderName}"

python ${flownet2Nvidia}/main.py --inference --model FlowNet2 --save_flow \
--inference_dataset ImagesFromFolder \
--inference_dataset_root ${framesdir} \
--resume ${flownet2Nvidia}/checkpoints/FlowNet2_checkpoint.pth.tar \
--save ${folderName}/forward \
--inference_visualize

python ${flownet2Nvidia}/main.py --inference --model FlowNet2 --save_flow \
--inference_dataset ImagesFromFolder \
--inference_dataset_root ${framesdir} \
--resume ${flownet2Nvidia}/checkpoints/FlowNet2_checkpoint.pth.tar \
--save ${folderName}/backward \
--inference_visualize --backward

python ${workdir}/prepare_flownames.py --path ${folderName}/forward
mv -t ${folderName} ${folderName}/forward/*.flo 
rm -r ${folderName}/forward/
python ${workdir}/prepare_flownames.py --path ${folderName}/backward --backward
mv -t ${folderName} ${folderName}/backward/*.flo
rm -r ${folderName}/backward/

i=$[$startFrame]
j=$[$startFrame + $stepSize]

while true; do
  file1=$(printf "$filePattern" "$i")
  file2=$(printf "$filePattern" "$j")
  if [ -a $file2 ]; then
    ./consistencyChecker/consistencyChecker "${folderName}/backward_${j}_${i}.flo" "${folderName}/forward_${i}_${j}.flo" "${folderName}/reliable_${j}_${i}.pgm"
    ./consistencyChecker/consistencyChecker "${folderName}/forward_${i}_${j}.flo" "${folderName}/backward_${j}_${i}.flo" "${folderName}/reliable_${i}_${j}.pgm"
  else
    break
  fi
  i=$[$i +1]
  j=$[$j +1]
done
