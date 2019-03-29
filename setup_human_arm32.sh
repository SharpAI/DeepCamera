#!/bin/bash
  
if [ ! -f model/net2.params ]; then
  echo need download model for embedding
  wget https://github.com/solderzzc/sharpai/releases/download/human2.0/model_human_arm32.tar.gz
  tar -xvf model_human_arm32.tar.gz
  rm model_human_arm32.tar.gz
fi

cd src/detector_human
npm install
cd -
cd src/monitor
npm install
