#!/bin/bash

if [ ! -f model/net2.params ]; then
  echo need download model for embedding
  mkdir model
  cd model
  wget https://github.com/solderzzc/model_release/releases/download/v1.0/model-armv7a.tgz
  tar -xvf model-armv7a.tgz
  rm model-armv7a.tgz
  cd ..
fi

cd src/detector
npm install
cd -
cd src/monitor
npm install

cd -
cd src/flower
pip2 install -r requirements.txt
