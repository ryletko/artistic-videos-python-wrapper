import yaml
import shutil
import os
import subprocess
import glob

def dowork():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    config_file_path=os.path.join(dir_path, "stylize.config")

    config_obj = None
    with open(config_file_path, 'r') as stream:
        try:
            config_obj = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)

    video_path = config_obj["video_path"]
    styles_path = config_obj["styles_path"]
    work_name = os.path.basename(video_path).split('.')[0]
    if len(work_name) <= 0:
        return

    work_path = os.path.join(dir_path, work_name)
    frames_path = os.path.join(work_path, "frames")
    # output_path = os.path.join(work_path, "output")
    resolution = config_obj["resolution"]
    frames_count = config_obj["frames_count"] 
    extract_frames_mask = f"{frames_path}/frame_%04d.png"
    torch_path = config_obj["torch_path"]
    style_weight = config_obj["style_weight"]
    temporal_weight = config_obj["temporal_weight"]
    out_dir = os.path.join(work_path, "out")

    if (config_obj["clean"] == True and os.path.exists(work_path)):
        shutil.rmtree(work_path)

    if (not os.path.exists(work_path)):
        os.mkdir(work_path)    
        os.mkdir(frames_path)

    if (config_obj["frames"] == True):
        if (frames_count > 0):
            frames_in_video = 0
            process = subprocess.Popen(f"ffprobe -v error -select_streams v:0 -show_entries stream=nb_frames -of default=nokey=1:noprint_wrappers=1 {video_path}", stdout=subprocess.PIPE, shell=True)
            output, error = process.communicate()
            frames_in_video = int(output)
            extract_from = frames_in_video / 2 - frames_count / 2
            extract_to = extract_from + frames_count - 1
            ext_cmd = f"ffmpeg -i '{video_path}' -vf 'select=between(n\\,{extract_from:.0f}\\,{extract_to:.0f}),scale={resolution}' '{extract_frames_mask}'"
            print(ext_cmd)
            process = subprocess.Popen(ext_cmd, stdout=subprocess.PIPE, shell=True) 
            output, error = process.communicate()
            print(output)
        else:
            process = subprocess.Popen(f"ffmpeg -i '{video_path}' -vf scale='{resolution}' '{extract_frames_mask}'", stdout=subprocess.PIPE, shell=True) 
            output, error = process.communicate()
            print(output)

    if (config_obj["optflow"] == True):
        makeOptFlowScript = os.path.join(dir_path, "makeOptFlow.sh")
        prepareflownames_py = os.path.join(dir_path, "prepare_flownames.py")
        process = subprocess.check_call([ makeOptFlowScript, dir_path, frames_path, extract_frames_mask, f"{work_path}/flow_{resolution}/", prepareflownames_py ])

    if (not os.path.exists(out_dir)):
        os.mkdir(out_dir)

    styles = glob.glob(os.path.join(styles_path, "*.jpg"))
    for i in styles: 
        print(i)
        style_name = os.path.basename(i).split('.')[0]
        style_output_path = os.path.join(out_dir, style_name)
        if (not os.path.exists(style_output_path)):
            os.mkdir(style_output_path)
        torch_cmd = f"{torch_path} {dir_path}/artistic_video.lua \
            -content_pattern {extract_frames_mask} \
            -flow_pattern {work_path}/flow_{resolution}/backward_[%d]_{{%d}}.flo \
            -flowWeight_pattern {work_path}/flow_{resolution}/reliable_[%d]_{{%d}}.pgm \
            -style_weight {style_weight} \
            -temporal_weight {temporal_weight} \
            -output_folder {style_output_path}/ \
            -style_image {i} \
            -backend cudnn \
            -gpu 0 \
            -cudnn_autotune \
            -number_format %04d"
        print(torch_cmd)
        process = subprocess.Popen(torch_cmd, stdout=subprocess.PIPE, shell=True, cwd=dir_path) 
        output, error = process.communicate()
        print(output)
        if (config_obj["make_video"] == True):
            subprocess.Popen(f"ffmpeg -f image2 -i '{style_output_path}/out-%04d.png' -r 30 -q:v 1 -c:v mpeg4 '{style_output_path}out.mp4'", stdout=subprocess.PIPE, shell=True) 

    # process = subprocess.Popen(f"ffmpeg -i '{video_path}' -vf scale='{resolution}' '{frames_path}/frame_%04d.png'", stdout=subprocess.PIPE, shell=True) 
    # output, error = process.communicate()
    # print(output)

dowork()