#!/bin/bash
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$PREFIX/lib64
export DATA_RUNTIME_FOLDER=../model
export DEVICE_GROUP_ID_FILEPATH=/data/data/com.termux/files/home/.groupid.txt
export DEVICE_UUID_FILEPATH=/data/data/com.termux/files/home/.ro_serialno
export RUNTIME_BASEDIR=/data/data/com.termux/files/home/runtime
cd bin
while [ 1 ]
do
    TASKER=worker WORKER_TYPE=classify REDIS_ADDRESS=localhost ./classifier worker --loglevel INFO -E -n classify -c 1 -Q classify
  sleep 20
done
