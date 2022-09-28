#!/bin/bash

docker buildx build --push --platform linux/amd64,linux/arm64 --tag shareai/yolov7_reid:latest .

docker buildx build --build-arg JETPACK_VERSION=4 --build-arg SKIP_MINICONDA=true --build-arg UBUNTU_BASE_IMG=nvcr.io/nvidia/l4t-ml:r32.6.1-py3 --platform linux/arm64 --tag shareai/yolov7_reid:r32.6.1_latest .
docker buildx build --build-arg JETPACK_VERSION=5.0 --build-arg SKIP_MINICONDA=true --build-arg UBUNTU_BASE_IMG=nvcr.io/nvidia/l4t-ml:r35.1.0-py3 --platform linux/arm64 --tag shareai/yolov7_reid:r35.1.0_latest .
