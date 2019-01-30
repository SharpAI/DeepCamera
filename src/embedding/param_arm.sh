#!/usr/bin/env bash
export RUNTIME_BASEDIR=`pwd`
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$PREFIX/lib

while [ 1 ]
do
    LD_PRELOAD=libatomic.so:libcutils.so python2 parameter_server.py
    sleep 20
done
