#!/bin/bash

cd model
wget https://github.com/solderzzc/model_release/releases/download/v1.0/model-r50-am-lfw.tgz
tar -xvf model-r50-am-lfw.tgz
rm model-r50-am-lfw.tgz

