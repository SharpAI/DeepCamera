#!/bin/bash

export DEVICE_UUID_FILEPATH=/data/data/com.termux/files/home/.ro_serialno
export DEVICE_GROUP_ID_FILEPATH=/data/data/com.termux/files/home/.groupid.txt
export RUNTIME_BASEDIR=`pwd`

while [ 1 ]
do
  LD_PRELOAD=$LD_PRELOAD:libatomic.so:libcutils.so LD_LIBRARY_PATH=/system/lib:$LD_LIBRARY_PATH:$PREFIX/lib:/system/vendor/lib/egl DATA_RUNTIME_FOLDER=../../model WORKER_TYPE=embedding REDIS_ADDRESS=localhost WORKER_BROKER=redis://localhost/0 python2 upload_api-v2.py worker --loglevel INFO -E -n embedding -c 1 -Q embedding
  sleep 20
done
