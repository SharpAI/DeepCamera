#!/usr/bin/env bash
export RUNTIME_BASEDIR=`pwd`
export LD_LIBRARY_PATH=/system/lib:$LD_LIBRARY_PATH:$PREFIX/lib:/system/vendor/lib/egl
export DATA_RUNTIME_FOLDER=../model
export DEVICE_UUID_FILEPATH=/data/data/com.termux/files/home/.ro_serialno
export DEVICE_GROUP_ID_FILEPATH=/data/data/com.termux/files/home/.groupid.txt
#export LD_PRELOAD=$LD_PRELOAD:libatomic.so:libcutils.so
cd bin
while [ 1 ]
do
    LD_PRELOAD=libatomic.so:libcutils.so WORKER_TYPE=embedding REDIS_ADDRESS=localhost WORKER_BROKER=redis://localhost/0 ./embedding worker --loglevel INFO -E -n embedding -c 1 -Q embedding
    sleep 20
done
