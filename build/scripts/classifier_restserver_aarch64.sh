#!/usr/bin/env bash
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$PREFIX/lib64
export DATA_RUNTIME_FOLDER=../model
export DEVICE_GROUP_ID_FILEPATH=/data/data/com.termux/files/home/.groupid.txt
export DEVICE_UUID_FILEPATH=/data/data/com.termux/files/home/.ro_serialno 
export RUNTIME_BASEDIR=/data/data/com.termux/files/home/runtime
cd bin
while [ 1 ]
do
    TASKER=restserver REDIS_ADDRESS=localhost ./classifier
    sleep 20
done
