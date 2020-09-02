FROM shareai/tensorflow:armv7l_tf1.8
ENV DEBIAN_FRONTEND noninteractive

RUN apt-get install --no-install-recommends  -y python python-pip python-opencv python-dev \
    zlib1g-dev gcc python-pil && \
    apt-get clean
ADD face_detector /root/detector
WORKDIR /root/detector/
RUN python setup.py install
RUN python ./test.py
