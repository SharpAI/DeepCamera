#!/usr/bin/env bash
export RUNTIME_BASEDIR=`pwd`
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$PREFIX/lib64
export DATA_RUNTIME_FOLDER=../model
cd bin
while [ 1 ]
do
    ./param
    sleep 20
done
