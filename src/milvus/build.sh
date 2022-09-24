#!/bin/bash

docker build -t shareai/milvus:arm64_base -f Dockerfile.arm64_base .
docker build -t shareai/milvus:arm64_latest -f Dockerfile.arm64_deploy .