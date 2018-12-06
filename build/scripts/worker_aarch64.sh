#!/usr/bin/env bash
export RUNTIME_BASEDIR=`pwd`
export LD_LIBRARY_PATH=$PREFIX/lib64:$PREFIX/lib
export DATA_RUNTIME_FOLDER=../model
cd bin
while [ 1 ]
do
  ./worker worker --loglevel INFO -E -n detect -c 1 -Q detect
  sleep 20
done
