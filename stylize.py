import yaml
import shutil
import os
import subprocess
import glob
import utils.flow_utils as fu

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
    content_weights = config_obj["content_weight"].split(",")
    style_weights = config_obj["style_weight"].split(",")
    temporal_weight = config_obj["temporal_weight"]
    style_scales = config_obj["style_scale"].split(",")
    tv_weights = config_obj["tv_weight"].split(",")
    out_dir = os.path.join(work_path, "out")
    flownet2_nvidia = config_obj["flownet2_nvidia_path"]
    conda_env = config_obj["conda_env"]
    multipass = config_obj["multipass"]
    continue_with = config_obj["continue_with"]
    continue_with_pass = config_obj["continue_with_pass"]
    num_passes = config_obj["num_passes"]

    flow_path = f"{work_path}/flow_{resolution}/"

    if (config_obj["clean"] == True and os.path.exists(work_path)):
       if (input(f"Are you sure you want to delete {work_path}: ") == "y"):
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
        process = subprocess.check_call([ makeOptFlowScript, dir_path, frames_path, extract_frames_mask, flow_path, flownet2_nvidia, conda_env  ])
        flows = glob.glob(os.path.join(flow_path, "*.flo"))
        for f in flows:
            fu.visulize_flow_file(f, flow_path)

    if (not os.path.exists(out_dir)):
        os.mkdir(out_dir)

    styles = sorted(glob.glob(os.path.join(styles_path, "*.jpg")))
    for i in styles: 
        for content_weight in content_weights:
            for style_weight in style_weights:
                for style_scale in style_scales:
                    for tv_weight in tv_weights:
                        print(i)
                        style_name = os.path.basename(i).split('.')[0]
                        style_output_path = os.path.join(out_dir, f"{style_name}_cw_{content_weight}_sw_{style_weight}_ss_{style_scale}_tv_{tv_weight}")
                        if (not os.path.exists(style_output_path)):
                            os.mkdir(style_output_path)
                        if (multipass):
                            torch_cmd = f"{torch_path} {dir_path}/artistic_video_multiPass.lua \
                                -content_pattern {extract_frames_mask} \
                                -backwardFlow_pattern {flow_path}/backward_[%d]_{{%d}}.flo \
                                -backwardFlow_weight_pattern {flow_path}/reliable_[%d]_{{%d}}.pgm \
                                -forwardFlow_pattern {flow_path}/forward_[%d]_{{%d}}.flo \
                                -forwardFlow_weight_pattern {flow_path}/reliable_[%d]_{{%d}}.pgm \
                                -content_weight {content_weight} \
                                -style_weight {style_weight} \
                                -temporal_weight {temporal_weight} \
                                -style_scale {style_scale} \
                                -tv_weight {tv_weight} \
                                -output_folder {style_output_path}/ \
                                -style_image {i} \
                                -backend cudnn \
                                -gpu 0 \
                                -cudnn_autotune \
                                -number_format %04d \
                                -continue_with_pass {continue_with_pass} \
                                -num_passes {num_passes}"
                        else:
                            torch_cmd = f"{torch_path} {dir_path}/artistic_video.lua \
                                -content_pattern {extract_frames_mask} \
                                -flow_pattern {flow_path}/backward_[%d]_{{%d}}.flo \
                                -flowWeight_pattern {flow_path}/reliable_[%d]_{{%d}}.pgm \
                                -content_weight {content_weight} \
                                -style_weight {style_weight} \
                                -temporal_weight {temporal_weight} \
                                -style_scale {style_scale} \
                                -output_folder {style_output_path}/ \
                                -style_image {i} \
                                -continue_with {continue_with} \
                                -backend cudnn \
                                -gpu 0 \
                                -cudnn_autotune \
                                -number_format %04d"
                        print(torch_cmd)
                        process = subprocess.Popen(torch_cmd, stdout=subprocess.PIPE, shell=True, cwd=dir_path, universal_newlines=True)
                        while True:
                            output = process.stdout.readline()
                            print(output.strip())
                            # Do something else
                            return_code = process.poll()
                            if return_code is not None:
                                print('RETURN CODE', return_code)
                                # Process has finished, read rest of the output 
                                for output in process.stdout.readlines():
                                    print(output.strip())
                                break       
                        # output, error = process.communicate()
                        # print(output)
                        if (config_obj["make_video"] == True):
                            subprocess.Popen(f"ffmpeg -f image2 -i '{style_output_path}/out-%04d.png' -r 30 -q:v 1 -c:v mpeg4 '{style_output_path}out.mp4'", stdout=subprocess.PIPE, shell=True) 

    # process = subprocess.Popen(f"ffmpeg -i '{video_path}' -vf scale='{resolution}' '{frames_path}/frame_%04d.png'", stdout=subprocess.PIPE, shell=True) 
    # output, error = process.communicate()
    # print(output)

dowork()
