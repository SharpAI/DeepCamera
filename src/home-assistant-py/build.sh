#!/bin/bash
# remove support of linux/arm/v6,linux/386
# reference link: https://www.smartling.com/resources/product/building-multi-architecture-docker-images-on-arm-64-bit-aws-graviton2/

echo 'Building for Python backend'
docker buildx build --platform linux/amd64,linux/arm64/v8,linux/arm/v7 -t shareai/home-assiistant-py:2022.8 --push . 
