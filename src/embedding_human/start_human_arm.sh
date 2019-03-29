#!/bin/bash

#export RUNTIME_BASEDIR=`pwd`
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$PREFIX/lib:/system/vendor/lib/egl
export DEVICE_UUID_FILEPATH=/data/data/com.termux/files/home/.ro_serialno
export DEVICE_GROUP_ID_FILEPATH=/data/data/com.termux/files/home/.groupid.txt
export LD_PRELOAD=$LD_PRELOAD:libatomic.so:libcutils.so

python2 parameter_server.py &

python2 migrate_db.py db upgrade

#TASKER=worker WORKER_TYPE=classify REDIS_ADDRESS=localhost python2 classifier_rest_server.py worker --loglevel INFO -E -n classify -c 1 -Q classify &
#TASKER=restserver REDIS_ADDRESS=localhost python2 classifier_rest_server.py &

DATA_RUNTIME_FOLDER=../../model WORKER_TYPE=embedding CLUSTER_REDIS_ADDRESS=localhost CLUSTER_REDIS_PORT=6379 REDIS_ADDRESS=localhost WORKER_BROKER=redis://localhost/0 python2 upload_api-v2_human.py worker --loglevel INFO -E -n embedding -c 1 -Q embedding
