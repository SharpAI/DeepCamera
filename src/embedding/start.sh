#!/bin/bash

if [ -f migrate_db.py ]; then
  python migrate_db.py db upgrade
else
  if [ -f migrate_db.pyc ]; then
    python migrate_db.pyc db upgrade
  else
    if [ -f migrate_db.exe ]; then
      ./migrate_db.exe db upgrade
    fi
  fi
fi

if [ -f upload_api-v2.py ]; then
  WORKER_TYPE=detect python upload_api-v2.py worker --loglevel INFO -E -n detect -c 1 -Q detect &
  WORKER_TYPE=embedding python upload_api-v2.py worker --loglevel INFO -E -n embedding -c 1 -Q embedding &
else
  if [ -f /usr/local/lib/libjemalloc.so ]; then
    LD_PRELOAD=/usr/local/lib/libjemalloc.so WORKER_TYPE=detect ./upload_api-v2.exe worker --loglevel INFO -E -n detect -c 1 -Q detect &
    LD_PRELOAD=/usr/local/lib/libjemalloc.so WORKER_TYPE=embedding ./upload_api-v2.exe worker --loglevel INFO -E -n embedding -c 1 -Q embedding &
  else
    WORKER_TYPE=detect ./upload_api-v2.exe worker --loglevel INFO -E -n detect -c 1 -Q detect &
    WORKER_TYPE=embedding ./upload_api-v2.exe worker --loglevel INFO -E -n embedding -c 1 -Q embedding &
  fi
fi
while [ 1 ]
do
  sleep 20
done
