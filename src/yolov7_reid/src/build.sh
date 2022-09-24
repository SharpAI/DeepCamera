#!/bin/bash

docker buildx build --push --platform linux/amd64,linux/arm64 --tag shareai/yolov7_reid:latest .
