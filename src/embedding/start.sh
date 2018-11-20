#!/bin/bash

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
  LD_LIBRARY_PATH=/system/lib64:$LD_LIBRARY_PATH:$PREFIX/lib64 python2 classifier_rest_server.py &
else
  if [ -f classifier_rest_server.pyc ]; then
    LD_LIBRARY_PATH=/system/lib64:$LD_LIBRARY_PATH:$PREFIX/lib64 python2 classifier_rest_server.pyc &
  else
    if [ -f classifier_rest_server.exe ]; then
      LD_LIBRARY_PATH=/system/lib64:$LD_LIBRARY_PATH:$PREFIX/lib64 ./classifier_rest_server.exe &
    fi
  fi
fi

while [ 1 ]
do
  if [ -f upload_api-v2.py ]; then
    LD_LIBRARY_PATH=/system/lib64:$LD_LIBRARY_PATH:$PREFIX/lib64 DATA_RUNTIME_FOLDER=../../model WORKER_TYPE=embedding REDIS_ADDRESS=localhost WORKER_BROKER=redis://localhost/0 python2 upload_api-v2.py worker --loglevel INFO -E -n embedding -c 1 -Q embedding
  elif [ -f upload_api-v2.pyc ]; then
    LD_LIBRARY_PATH=/system/lib64:$LD_LIBRARY_PATH:$PREFIX/lib64 DATA_RUNTIME_FOLDER=../../model WORKER_TYPE=embedding REDIS_ADDRESS=localhost WORKER_BROKER=redis://localhost/0 python2 upload_api-v2.pyc worker --loglevel INFO -E -n embedding -c 1 -Q embedding
  else
    LD_LIBRARY_PATH=/system/lib64:$LD_LIBRARY_PATH:$PREFIX/lib64 DATA_RUNTIME_FOLDER=../../model WORKER_TYPE=embedding REDIS_ADDRESS=localhost WORKER_BROKER=redis://localhost/0 ./upload_api-v2.exe worker --loglevel INFO -E -n embedding -c 1 -Q embedding
  fi
  sleep 20
done
