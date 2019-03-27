#!/bin/bash
cpwd=$(pwd)
while [ 1 ]
do
  $PREFIX/bin/bash /data/data/com.termux/files/home/arch/startarch c "cd "${cpwd}" && CLUSTER_REDIS_ADDRESS=localhost CLUSTER_REDIS_PORT=6379 CLUSTER_CONCURRENCY=80 DEVICE_GROUP_ID_FILEPATH=/data/data/com.termux/files/home/.groupid.txt DEVICE_UUID_FILEPATH=/data/data/com.termux/files/home/.ro_serialno TASKER=restserver REDIS_ADDRESS=localhost RUNTIME_BASEDIR=/data/data/com.termux/files/home/runtime python classifier_rest_server.py"
  sleep 20
done
