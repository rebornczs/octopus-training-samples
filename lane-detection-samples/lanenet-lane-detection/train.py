# -*- coding: utf-8 -*-
import os
import sys
import subprocess

if __name__ == "__main__":
    algorithm_dir = os.path.dirname(os.path.realpath(__file__))
    dataset_name = os.listdir("/tmp/data/dataset/dataset-0")[0]
    dataset_dir = os.path.join("/tmp/data/dataset/dataset-0", dataset_name)

    # 拷贝原始数据集到当前目录 ***
    process = subprocess.Popen(f"cp -r {dataset_dir} {algorithm_dir}/dataset", shell=True)
    ret = process.wait()
    if ret != 0:
        sys.exit(1)
    # 构建lanenet数据集
    process = subprocess.Popen(f"python tools/generate_tusimple_dataset.py --src_dir {algorithm_dir}/dataset",
                               shell=True)
    ret = process.wait()
    if ret != 0:
        sys.exit(1)
    # 构建tf record文件
    process = subprocess.Popen("python tools/make_tusimple_tfrecords.py", shell=True)
    ret = process.wait()
    if ret != 0:
        sys.exit(1)
    # 运行训练脚本
    process = subprocess.Popen("python tools/train_lanenet_tusimple.py", shell=True)
    ret = process.wait()
    if ret != 0:
        sys.exit(1)
    # 拷贝产物路径至上传路径 ***
    process = subprocess.Popen("rm -rf dataset && cp -r * /tmp/res", shell=True)
    ret = process.wait()
    if ret != 0:
        sys.exit(1)
