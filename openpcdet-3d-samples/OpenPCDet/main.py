import subprocess
import sys

def main():
    cmd = "python -m pcdet.datasets.kitti.kitti_dataset " \
        "create_kitti_infos tools/cfgs/dataset.yaml" \
        "&& cd tools && python train.py"
    cmd += " ".join(sys.argv[1:])
    print(cmd)
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIP, stderr=subprocess.STDOUT)
    while p.poll() is None:
        line = p.stdout.readline.decode("utf-8")
        print(line)
    
if __name__ == "__main__":
    main()
