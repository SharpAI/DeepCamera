#!/usr/bin/env bash
export RUNTIME_BASEDIR=`pwd`
export LD_LIBRARY_PATH=/system/lib64:$LD_LIBRARY_PATH:$PREFIX/lib64:/system/vendor/lib64/egl:/system/vendor/lib64
export DATA_RUNTIME_FOLDER=../model
export DEVICE_UUID_FILEPATH=/data/data/com.termux/files/home/.ro_serialno
export DEVICE_GROUP_ID_FILEPATH=/data/data/com.termux/files/home/.groupid.txt
export RUNTIME_BASEDIR=/data/data/com.termux/files/home/runtime
export CLUSTER_REDIS_ADDRESS=localhost
export CLUSTER_REDIS_PORT=6379
export CLUSTER_CONCURRENCY=1
cd bin
while [ 1 ]
do
    WORKER_TYPE=embedding REDIS_ADDRESS=localhost WORKER_BROKER=redis://localhost/0 ./embedding worker --loglevel INFO -E -n embedding -c 1 -Q embedding
    sleep 20
done
