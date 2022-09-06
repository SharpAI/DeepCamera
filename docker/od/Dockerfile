FROM shareai/tensorflow:armv7l_tf1.8

WORKDIR /root
ENV PYTHONPATH /root/models/research/object_detection:/root/models/research:/root/models/research/slim
ADD ./models /root/models
WORKDIR /root
RUN apt-get update && apt-get install -y autoconf automake libtool curl make g++ unzip
COPY ./protobuf-all-3.5.1.tar.gz /root/protobuf-all-3.5.1.tar.gz
RUN tar -zxvf protobuf-all-3.5.1.tar.gz 
WORKDIR /root/protobuf-3.5.1
RUN    ls -alh && \
       ./autogen.sh && \
       ./configure && \
       make && \
       make check && \
       make install && \
       ldconfig
WORKDIR /root/models/research
RUN protoc object_detection/protos/*.proto --python_out=.

WORKDIR /root
ADD ./assets/models/ssdlite_mobilenet_v2_coco_2018_05_09/frozen_inference_graph.pb /root/ssdlite_mobilenet_v2_coco_2018_05_09/frozen_inference_graph.pb
ADD ./assets/labelmap.prototxt /root/ssdlite_mobilenet_v2_coco_2018_05_09/

ADD requirements.txt /root/
RUN pip install -r /root/requirements.txt
ADD od.py /root/
ADD panda.jpg /root/
WORKDIR /root
#clean up
RUN apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* && \
    rm -rf /root/.cache/pip/
# RUN PYTHONPATH="/root/models/research/object_detection:/root/models/research:/root/models/research/slim" python od.py worker --loglevel INFO -E -n od -c 1 -Q od
