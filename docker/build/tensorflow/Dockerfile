FROM arm32v7/debian:stretch

# ADD sources.list  /etc/apt/sources.list
#RUN echo "nameserver 8.8.8.8" > /etc/resolv.conf
#RUN cat /etc/resolv.conf
#ADD tensorflow-1.8.0-cp27-none-linux_aarch64.whl /tensorflow-1.8.0-cp27-none-linux_aarch64.whl
RUN cp /etc/apt/sources.list /etc/apt/sources.list.bk && \
    echo "deb http://ftp2.cn.debian.org/debian/ stretch main non-free contrib"           >  /etc/apt/sources.list && \
    echo "deb http://ftp2.cn.debian.org/debian/ stretch-updates main non-free contrib"   >> /etc/apt/sources.list && \
    echo "deb http://ftp2.cn.debian.org/debian/ stretch-backports main non-free contrib" >> /etc/apt/sources.list && \
    apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y python-pip python-opencv python-matplotlib \
    python-scipy python-h5py python-requests python-psutil git cmake wget unzip \
    python-sklearn python-numpy curl wget python-pil python-skimage \
    zlib1g-dev libjpeg-dev libtiff5-dev && \
    curl -O https://bootstrap.pypa.io/get-pip.py && \
    python get-pip.py && \
    rm get-pip.py
#RUN cd / && wget https://github.com/lhelontra/tensorflow-on-arm/releases/download/v1.8.0/tensorflow-1.8.0-cp27-none-linux_armv7l.whl 
ADD tensorflow-1.8.0-cp27-none-linux_armv7l.whl /tensorflow-1.8.0-cp27-none-linux_armv7l.whl
ADD assets/requirements.txt /root/requirements.txt
ADD assets/test.py /test.py

RUN pip install --ignore-installed -i https://pypi.tuna.tsinghua.edu.cn/simple /tensorflow-1.8.0-cp27-none-linux_armv7l.whl && \
    pip install --ignore-installed -i https://pypi.tuna.tsinghua.edu.cn/simple -r /root/requirements.txt && rm /root/requirements.txt && \
    python /test.py && \
    apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* && \
    rm -rf /root/.cache/pip/ && rm -rf /*.whl && rm /test.py && \
    cp /etc/apt/sources.list.bk /etc/apt/sources.list
