# YOLOv5 🚀 by Ultralytics, GPL-3.0 license
FROM nvidia/cuda:11.0.3-devel-ubuntu18.04

# Install linux packages
RUN rm -rf /home/work
RUN mkdir /home/cache
RUN mkdir -p /root/.config/Ultralytics
WORKDIR /home
COPY docker/docker_xiangjiang/files/work ./work
COPY docker/docker_xiangjiang/files/common ./common
COPY docker/docker_xiangjiang/files/third_party_sdk ./third_party_sdk
COPY docker/docker_xiangjiang/files/conf ./conf
COPY docker/docker_xiangjiang/files/dls-key-client /usr/bin/dls-key-client
COPY docker/docker_xiangjiang/files/Arial.ttf /root/.config/Ultralytics/Arial.ttf
COPY docker/docker_xiangjiang/pip.conf /root/.pip/pip.conf
# COPY ./sources.list /etc/apt/sources.list
COPY detection-2d-samples/2.yolov5/requirements.txt /root/requirements.txt

RUN rm -rf /etc/apt/sources.list.d/* && \
        apt -y update && \
        apt-get install -y build-essential protobuf-compiler libpq-dev alien && \
        apt-get install -y apt-utils git curl ca-certificates zip tree htop wget && \
        apt -y install python3.8 python3-pip python3.8-dev && \
        echo alias python=python3 >> ~/.bashrc && echo alias pip=pip3 >> ~/.bashrc && \
        apt -y install python libgl1-mesa-glx libglib2.0-0 libxext6 libxrender-dev bmon iotop g++ && \
        rm -f /usr/bin/python && \
        ln -s /usr/bin/python3.8 /usr/bin/python && \
        rm -f /usr/bin/python3 && \
        ln -s /usr/bin/python3.8 /usr/bin/python3

RUN echo "/home/third_party_sdk/obs_sdk/src" > /usr/local/lib/python3.8/dist-packages/obs-python-sdk.pth
RUN python -m pip install --upgrade pip && pip3 install --upgrade setuptools
RUN pip3 install --user -r /root/requirements.txt
RUN pip --no-cache-dir install Cython pytest-runner==5.1 boto3 botocore netifaces zmq hyper
RUN pip --no-cache-dir install elasticsearch psycopg2 flask requests concurrent-log-handler
RUN chmod a+x /home/work/run_train_kubernetes.sh

# Python ENV
# ENV PYTHONBUFFERED 1
ENV PATH /opt/octopus/tools/miniconda3/bin/:/home/work/:/home/:$PATH
ENV LD_LIBRARY_PATH /opt/octopus/tools/lib:$LD_LIBRARY_PATH
ENV PYTHONPATH /home/work:$PYTHONPATH
ENV PYTHONPATH /home/work/octopus:$PYTHONPATH
ENV PYTHONPATH /home/:$PYTHONPATH

