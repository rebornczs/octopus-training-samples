#!/usr/bin/bash
# use python2
# export FUXI_INST_ID=53475980774144

set -ex

echo "==================================="

# 镜像名称
image_name=octopus-evaluate-core

# 镜像版本(tag)
version=0.0.1

# 镜像地址
url=registry-cbu.huawei.com/ivehicle/$image_name:$version

# 镜像sha256，目前没有做校验
sha256=cac7fac5a6b0f450e85865fdb468e06acef0bc6e81645a7130fcda871f1c505a

if [ $FUXI_INST_ID ];then
echo "伏羲流水线ID:" $FUXI_INST_ID
#wget -N --no-check-certificate https://obs.devcloud.huawei.com/buildbox/generate_metadata_paas.py
#wget -N --no-check-certificate https://obs.devcloud.huawei.com/buildbox/upload_metadata.py
echo ">>>> 开始生成 metadata.json"
python generate_metadata_paas.py -p image -n $image_name -v $version -u $url -m $sha256
echo ">>>> 开始上传元数据中心"
python upload_metadata.py -u -g    #*备注：-g  上传绿区环境 *
else
    echo "没有收到流水线ID"
    exit 1
fi