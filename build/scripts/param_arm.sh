#!/usr/bin/env bash
export RUNTIME_BASEDIR=`pwd`
export LD_LIBRARY_PATH=/system/lib:$LD_LIBRARY_PATH:$PREFIX/lib

cd bin
while [ 1 ]
do
    LD_PRELOAD=libatomic.so:libcutils.so ./param
    sleep 20
done
