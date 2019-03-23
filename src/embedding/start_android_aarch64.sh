#!/bin/bash

if [ ! -d ${RUNTIME_BASEDIR} ];then
    mkdir -p ${RUNTIME_BASEDIR}
fi

python2 parameter_server.py &
python2 migrate_db.py db upgrade

TASKER=restserver python2 classifier_rest_server.py &
TASKER=worker WORKER_TYPE=classify python2 classifier_rest_server.py worker --loglevel INFO -E -n classify -c 1 -Q classify &

if [ "$HAS_OPENCL" = "false" ]
then
  LD_LIBRARY_PATH=/system/lib64:$LD_LIBRARY_PATH:$PREFIX/lib64 python2 embedding_server.py &
fi

while [ 1 ]
do
  LD_LIBRARY_PATH=/system/lib64:$LD_LIBRARY_PATH:$PREFIX/lib64:/system/vendor/lib64/egl:/system/vendor/lib64 WORKER_TYPE=embedding python2 upload_api-v2.py worker --loglevel INFO -E -n embedding -c 1 -Q embedding
done
