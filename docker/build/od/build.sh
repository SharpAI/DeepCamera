#!/bin/bash

if [ ! -d models ]; then
  git clone https://github.com/tensorflow/models
fi

if [ ! -f protobuf-all-3.5.1.tar.gz ]; then
  wget https://github.com/google/protobuf/releases/download/v3.5.1/protobuf-all-3.5.1.tar.gz
fi

docker build -f Dockerfile -t shareai/od_worker:arm32v7 .
