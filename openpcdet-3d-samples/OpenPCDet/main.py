import subprocess
import sys
import os

def main():
    main_dir, _ = os.path.split(os.path.abspath(__file__))
    cmd = f"cd {main_dir} && python setup.py develop && " \
          f"python -m pcdet.datasets.kitti.kitti_dataset create_kitti_infos tools/cfgs/dataset_configs/kitti_dataset.yaml " \
          f"&& cd tools && python train.py --cfg_file cfgs/kitti_models/pointpillar.yaml"
    cmd += " ".join(sys.argv[1:])
    print(cmd)
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    while p.poll() is None:
        line = p.stdout.readline().decode("utf-8")
        print(line)
    
if __name__ == "__main__":
    main()
