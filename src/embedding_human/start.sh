#!/bin/bash

export DEVICE_UUID_FILEPATH=/data/data/com.termux/files/home/.ro_serialno
export DEVICE_GROUP_ID_FILEPATH=/data/data/com.termux/files/home/.groupid.txt
export RUNTIME_BASEDIR=/data/data/com.termux/files/home/runtime

if [ ! -d ${RUNTIME_BASEDIR} ];then
    mkdir -p ${RUNTIME_BASEDIR}
fi

if [ -f parameter_server.py ]; then
  python2 parameter_server.py &
else
  if [ -f parameter_server.pyc ]; then
    python2 parameter_server.pyc &
  else
    if [ -f parameter_server.exe ]; then
      ./parameter_server.exe &
    fi
  fi
fi

if [ -f migrate_db.py ]; then
  python2 migrate_db.py db upgrade
else
  if [ -f migrate_db.pyc ]; then
    python2 migrate_db.pyc db upgrade
  else
    if [ -f migrate_db.exe ]; then
      ./migrate_db.exe db upgrade
    fi
  fi
fi

if [ -f classifier_rest_server.py ]; then
  TASKER=restserver REDIS_ADDRESS=localhost python2 classifier_rest_server.py &
  TASKER=worker WORKER_TYPE=classify REDIS_ADDRESS=localhost python2 classifier_rest_server.py worker --loglevel INFO -E -n classify -c 1 -Q classify &
else
  if [ -f classifier_rest_server.pyc ]; then
    TASKER=restserver REDIS_ADDRESS=localhost python2 classifier_rest_server.pyc &
    TASKER=worker WORKER_TYPE=classify REDIS_ADDRESS=localhost python2 classifier_rest_server.pyc worker --loglevel INFO -E -n classify -c 1 -Q classify &
  else
    if [ -f classifier_rest_server.exe ]; then
      TASKER=restserver REDIS_ADDRESS=localhost ./classifier_rest_server.exe &
      TASKER=worker WORKER_TYPE=classify REDIS_ADDRESS=localhost ./classifier_rest_server.exe worker --loglevel INFO -E -n classify -c 1 -Q classify &
    fi
  fi
fi

while [ 1 ]
do
  if [ -f upload_api-v2.py ]; then
    LD_LIBRARY_PATH=/system/lib64:$LD_LIBRARY_PATH:$PREFIX/lib64 DATA_RUNTIME_FOLDER=../../model CLUSTER_REDIS_ADDRESS=localhost REDIS_ADDRESS=localhost WORKER_TYPE=embedding REDIS_ADDRESS=localhost WORKER_BROKER=redis://localhost/0 python2 upload_api-v2.py worker --loglevel INFO -E -n embedding -c 1 -Q embedding
  elif [ -f upload_api-v2.pyc ]; then
    LD_LIBRARY_PATH=/system/lib64:$LD_LIBRARY_PATH:$PREFIX/lib64 DATA_RUNTIME_FOLDER=../../model CLUSTER_REDIS_ADDRESS=localhost REDIS_ADDRESS=localhost WORKER_TYPE=embedding REDIS_ADDRESS=localhost WORKER_BROKER=redis://localhost/0 python2 upload_api-v2.pyc worker --loglevel INFO -E -n embedding -c 1 -Q embedding
  else
    LD_LIBRARY_PATH=/system/lib64:$LD_LIBRARY_PATH:$PREFIX/lib64 DATA_RUNTIME_FOLDER=../../model CLUSTER_REDIS_ADDRESS=localhost REDIS_ADDRESS=localhost WORKER_TYPE=embedding REDIS_ADDRESS=localhost WORKER_BROKER=redis://localhost/0 ./upload_api-v2.exe worker --loglevel INFO -E -n embedding -c 1 -Q embedding
  fi
  sleep 20
done
