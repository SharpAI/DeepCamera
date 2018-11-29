#!/usr/bin/env bash
export RUNTIME_BASEDIR=`pwd`
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$PREFIX/lib64
export DATA_RUNTIME_FOLDER=../../model
export DEVICE_UUID_FILEPATH=/data/data/com.termux/files/home/.ro_serialno
export DEVICE_GROUP_ID_FILEPATH=/data/data/com.termux/files/home/.groupid.txt
while [ 1 ]
do
    WORKER_TYPE=embedding REDIS_ADDRESS=localhost WORKER_BROKER=redis://localhost/0 python2 upload_api-v2.py worker --loglevel INFO -E -n embedding -c 1 -Q embedding
    sleep 20
done
