This is the python wrapper for [Artistic style transfer for videos](https://github.com/manuelruder/artistic-videos). It lets process a video or a part of it through a batch of styles in series.
I use it for choosing a style which fits the most to the video..

My environment is Ubuntu 18.04, CUDA 10.0 and Cudnn 7.6.5 drivers and GPU Nvidia RTX 2070 Super MAX-Q with 8 GB RAM.

For computing optical flow I use [NVidia Flownet 2 Pytorch](https://github.com/NVIDIA/flownet2-pytorch) set up in a separate Conda environment. Unlike DeepFlow, suggested in the original repository, FlowNet2 is much faster and doesn't require any RAM, because it utilizes Cudnn for the computation. It is nice for those who want to keep using the PC in parallel while the video is being stylized. I've slightly modified main.py to add backward processing which is enabled if --backward flag is presented, this means that the frames are interated in an opposite order.

There is an example of stylize.config file in the repo:

* Path to the original video:

  video_path: /home/anre/Videos/svia.mp4 

* Directory which contains all styles to process with:

  styles_path: /home/anre/artistic-videos-python-wrapper/styles/

* Resolution of the output (896x896 is optimal for 8GB RAM):

  resolution: 896x896

* Number of frames to stylize for partial processing (0 - all frames), they are extracted from the middle of the video:

  frames_count: 10

* Path to Torch7:

  torch_path: /home/anre/torch/install/bin/th

* Path to Flownet2 Pytorch:

  flownet2_nvidia_path: /home/anre/flownet2-nvidia/

* Conda environment which contains all dependencies for Flownet2 Pytorch: 

  conda_env: flownet-env

* Parameters described in the original repo [Artistic style transfer for videos](https://github.com/manuelruder/artistic-videos):

  style_weight: 1e3
  temporal_weight: 1e3

* Delete all previous outputs prior start:

  clean: true

* Compute optical flow:

  optflow: true

* Extract frames:

  frames: true

* Make final video:

  make_video: true

You can find my stylized videos [here](https://www.instagram.com/anre_rule/)