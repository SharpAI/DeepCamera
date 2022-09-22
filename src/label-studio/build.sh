#!/bin/bash
git clone https://github.com/heartexlabs/label-studio -b v1.5.0 
cd label-studio
docker buildx build --push --platform linux/amd64,linux/arm64 \
--tag sharpai/label-studio:1.5.0 .
