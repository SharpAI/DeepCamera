#!/bin/bash

if [ ! -f model/net2.params ]; then
  echo need download model for embedding
  wget https://github.com/solderzzc/model_release/releases/download/v1.0/model.tgz
  tar -xvf model.tgz
  rm model.tgz
fi

cd src/detector
npm install
cd -
cd src/monitor
npm install

