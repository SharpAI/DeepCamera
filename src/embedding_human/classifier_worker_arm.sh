#!/bin/bash
cpwd=$(pwd)
while [ 1 ]
do
  $PREFIX/bin/bash /data/data/com.termux/files/home/arch/startarch c "cd "${cpwd}" && TASKER=worker WORKER_TYPE=classify REDIS_ADDRESS=localhost DEVICE_GROUP_ID_FILEPATH=/data/data/com.termux/files/home/.groupid.txt DEVICE_UUID_FILEPATH=/data/data/com.termux/files/home/.ro_serialno RUNTIME_BASEDIR="${cpwd}" python classifier_rest_server.py worker --loglevel INFO -E -n classify -c 1 -Q classify"
  sleep 20
done
