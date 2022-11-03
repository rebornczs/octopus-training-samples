#! /bin/bash
DOCKERFILE=$1
echo $DOCKERFILE

NAME=$2
echo $NAME

VERSION=$3
echo $VERSION

docker build -f docker/$DOCKERFILE -t registry-cbu.huawei.com/ivehicle/$NAME:$VERSION .