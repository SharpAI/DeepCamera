#!/bin/bash

if [ -f parameter_server.py ]; then
  python2 parameter_server.py &
fi

if [ -f classifier_rest_server.py ]; then
  TASKER=worker WORKER_TYPE=classify python2 classifier_rest_server.py worker --loglevel INFO -E -n classify -c 1 -Q classify &
  TASKER=restserver python2 classifier_rest_server.py &
fi

if [ -f migrate_db.py ]; then
  python2 migrate_db.py db upgrade
fi

python2 embedding_server.py &

if [ -f upload_api-v2.py ]; then
  WORKER_TYPE=embedding python2 upload_api-v2.py worker --loglevel INFO -E -n embedding -c 1 -Q embedding &
fi

while [ 1 ]
do
  sleep 20
done
