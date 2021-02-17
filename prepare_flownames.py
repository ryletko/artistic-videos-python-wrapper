import os, argparse
from glob import glob
from os.path import *


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--path', default='', type=str, help='')
    parser.add_argument('--backward', action='store_true', help="barckward optical calc")

args = parser.parse_args()
root = args.path
backward = args.backward

flows = sorted(glob(join(root, f'inference/run.epoch-0-flow-field/*.flo')), reverse=backward)
for i in range(len(flows)):
    if (backward == False):
        os.rename(flows[i], join(root, f"forward_{i+1}_{(i+2)}.flo"))
    else:
        os.rename(flows[i], join(root, f"backward_{(i+2)}_{i+1}.flo"))

images = sorted(glob(join(root, f'inference/run.epoch-0-flow-vis/*.png')), reverse=backward)
for i in range(len(images)):
    if (backward == False):
        os.rename(images[i], join(root, f"forward_{i+1}_{(i+2)}.png"))
    else:
        os.rename(images[i], join(root, f"backward_{(i+2)}_{i+1}.png"))


print('Done!')