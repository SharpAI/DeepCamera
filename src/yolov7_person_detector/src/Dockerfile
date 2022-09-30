ARG UBUNTU_BASE_IMG=ubuntu:18.04
FROM $UBUNTU_BASE_IMG

ENV DEBIAN_FRONTEND "noninteractive"
ENV TZ "America/Los_Angeles"
# Install some basic utilities
RUN apt-get update && apt-get install -y \
    curl \
    ca-certificates \
    sudo \
    git \
    bzip2 \
    libx11-6 \
    libglib2.0-0 \
    tzdata \
    bash \
    fluxbox \
    git \
    net-tools \
    novnc \
    supervisor \
    x11vnc \
    xterm \
    xvfb \
    wget \
    python3-pip \
    ffmpeg \
    libsm6 \
    libxext6 \
    qt5dxcb-plugin
 #&& rm -rf /var/lib/apt/lists/*

ENV HOME=/root

# Install Miniconda and Python 3.8
ENV CONDA_AUTO_UPDATE_CONDA=false
# No CUDA-specific steps
ENV NO_CUDA=1
ENV PATH=/root/miniconda/bin:$PATH
RUN sudo apt-get install -y ffmpeg libsm6 libxext6
ARG TARGETPLATFORM
RUN case ${TARGETPLATFORM} in \
    "linux/arm64")  MINICONDA_ARCH=aarch64  ;; \
    *)              MINICONDA_ARCH=x86_64   ;; \
    esac && \
    curl -fsSL -v -o ~/miniconda.sh -O  "https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-${MINICONDA_ARCH}.sh" \
    && chmod +x ~/miniconda.sh \
    && ~/miniconda.sh -b -p ~/miniconda \
    && rm ~/miniconda.sh \
    && conda install -y python libopencv opencv py-opencv

ENV LANG=en_US.UTF-8 \
    LANGUAGE=en_US.UTF-8 \
    LC_ALL=C.UTF-8 \
    DISPLAY=:0.0 \
    DISPLAY_WIDTH=1024 \
    DISPLAY_HEIGHT=768 \
    RUN_XTERM=yes \
    RUN_FLUXBOX=yes
ARG JETPACK_VERSION

RUN pip3 install --upgrade pip
RUN pip3 install onnxruntime \
                python-telegram-bot==13.14 \
                notebook==6.4.12 \
                pymilvus==2.0.0 \
                youtube-dl==2020.12.2 \
                Flask==2.0.3 \
                redis==4.3.4 \
                pafy==0.5.5
WORKDIR /root 

ADD ./docker-novnc /app/docker-novnc
ADD ./models /app/models
ADD ./YOLOv7 /app/YOLOv7
ADD ./requirements.txt /app/requirements.txt
RUN pip3 install -r /app/requirements.txt
ADD ./*.py /app/

WORKDIR /app

CMD ["/app/docker-novnc/entrypoint.sh"]
EXPOSE 8080