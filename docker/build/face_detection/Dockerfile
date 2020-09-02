FROM shareai/tensorflow:armv7l_tf1.8
ENV DEBIAN_FRONTEND noninteractive

RUN apt-get install --no-install-recommends  -y python python-pip python-opencv python-dev \
    zlib1g-dev gcc python-pil && \
    apt-get clean
RUN apt-get update && apt-get install -y git scons cmake wget unzip curl build-essential \
    libprotobuf-dev protobuf-compiler libopencv-dev python-pip python-setuptools python-dev

ADD face_detector /root/detector
ADD mtcnn /root/mtcnn
ADD ncnn /root/ncnn
RUN cd /root/mtcnn && \
    mkdir build && cd build && \
    cmake ../ && make -j6 && \
    cd /root/ncnn && mkdir build && cd build && \
    cmake ../ && make -j6
RUN cp /root/mtcnn/build/src/libncnn.a /root/detector/lib/ncnn/libncnn.a

WORKDIR /root/detector/
RUN python setup.py install
RUN python ./test.py
ADD requirements.txt /root/requirements.txt
RUN pip install -r /root/requirements.txt
