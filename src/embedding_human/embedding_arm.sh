#!/usr/bin/env bash
export RUNTIME_BASEDIR=`pwd`
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$PREFIX/lib:/system/vendor/lib/egl
export DATA_RUNTIME_FOLDER=../../model
export DEVICE_UUID_FILEPATH=/data/data/com.termux/files/home/.ro_serialno
export DEVICE_GROUP_ID_FILEPATH=/data/data/com.termux/files/home/.groupid.txt
export CLUSTER_REDIS_ADDRESS=localhost
export CLUSTER_REDIS_PORT=6379
export CLUSTER_CONCURRENCY=1
#export LD_PRELOAD=$LD_PRELOAD:libatomic.so:libcutils.so
while [ 1 ]
do
    LD_PRELOAD=libatomic.so:libcutils.so:libm.so WORKER_TYPE=embedding CLUSTER_REDIS_ADDRESS=localhost REDIS_ADDRESS=localhost WORKER_BROKER=redis://localhost/0 python2 upload_api-v2.py worker --loglevel INFO -E -n embedding -c 1 -Q embedding
    sleep 20
done
