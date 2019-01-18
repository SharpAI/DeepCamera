#!/bin/bash

export DEVICE_UUID_FILEPATH=/data/data/com.termux/files/home/.ro_serialno
export DEVICE_GROUP_ID_FILEPATH=/data/data/com.termux/files/home/.groupid.txt

python2 parameter_server.py &

python2 migrate_db.py db upgrade

LD_LIBRARY_PATH=/system/lib64:$LD_LIBRARY_PATH:$PREFIX/lib64 TASKER=worker WORKER_TYPE=classify python2 classifier_rest_server.py worker --loglevel INFO -E -n classify -c 1 -Q classify &
LD_LIBRARY_PATH=/system/lib64:$LD_LIBRARY_PATH:$PREFIX/lib64 TASKER=restserver python2 classifier_rest_server.py &

LD_LIBRARY_PATH=/system/lib64:$LD_LIBRARY_PATH:$PREFIX/lib64 DATA_RUNTIME_FOLDER=../../model WORKER_TYPE=embedding REDIS_ADDRESS=localhost WORKER_BROKER=redis://localhost/0 python2 upload_api-v2_human.py worker --loglevel INFO -E -n embedding -c 1 -Q embedding

