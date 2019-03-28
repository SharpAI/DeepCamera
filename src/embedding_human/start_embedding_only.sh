#!/bin/bash
ls -alh
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

if [ -f classifier_rest_server.py ]; then
  TASKER=worker WORKER_TYPE=classify python2 classifier_rest_server.py worker --loglevel INFO -E -n classify -c 1 -Q classify &
  TASKER=restserver python2 classifier_rest_server.py &
else
  if [ -f classifier_rest_server.pyc ]; then
    TASKER=worker WORKER_TYPE=classify python2 classifier_rest_server.pyc worker --loglevel INFO -E -n classify -c 1 -Q classify &
    TASKER=restserver python2 classifier_rest_server.pyc &
  else
    if [ -f classifier_rest_server.exe ]; then
      TASKER=worker WORKER_TYPE=classify ./classifier_rest_server.exe worker --loglevel INFO -E -n classify -c 1 -Q classify &
      TASKER=restserver python2 classifier_rest_server.exe &
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

if [ -f upload_api-v2.py ]; then
  #WORKER_TYPE=detect python2 upload_api-v2.py worker --loglevel INFO -E -n detect -c 1 -Q detect &
  WORKER_TYPE=embedding python2 upload_api-v2.py worker --loglevel INFO -E -n embedding -c 1 -Q embedding &
elif [ -f upload_api-v2.pyc ]; then
  WORKER_TYPE=embedding python2 upload_api-v2.pyc worker --loglevel INFO -E -n embedding -c 1 -Q embedding &
else
  if [ -f /usr/local/lib/libjemalloc.so ]; then
    #LD_PRELOAD=/usr/local/lib/libjemalloc.so WORKER_TYPE=detect ./upload_api-v2.exe worker --loglevel INFO -E -n detect -c 1 -Q detect &
    LD_PRELOAD=/usr/local/lib/libjemalloc.so WORKER_TYPE=embedding ./upload_api-v2.exe worker --loglevel INFO -E -n embedding -c 1 -Q embedding &
  else
    #WORKER_TYPE=detect ./upload_api-v2.exe worker --loglevel INFO -E -n detect -c 1 -Q detect &
    WORKER_TYPE=embedding ./upload_api-v2.exe worker --loglevel INFO -E -n embedding -c 1 -Q embedding &
  fi
fi
while [ 1 ]
do
  sleep 20
done
