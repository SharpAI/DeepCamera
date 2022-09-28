#!/bin/bash
case ${TARGETPLATFORM} in \
    "linux/arm64")  MINICONDA_ARCH=aarch64  ;; \
    *)              MINICONDA_ARCH=x86_64   ;; \
esac && \
curl -fsSL -v -o ~/miniconda.sh -O  "https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-${MINICONDA_ARCH}.sh" \
&& chmod +x ~/miniconda.sh \
&& ~/miniconda.sh -b -p ~/miniconda \
&& rm ~/miniconda.sh \
&& conda install -y python libopencv opencv py-opencv