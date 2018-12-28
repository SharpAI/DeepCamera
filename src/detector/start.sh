#!/bin/bash

export DEVICE_UUID_FILEPATH=/data/data/com.termux/files/home/.ro_serialno
export DEVICE_GROUP_ID_FILEPATH=/data/data/com.termux/files/home/.groupid.txt
export UPLOAD_IMAGE_SERVICE_ENABLED=1
# export RUNTIME_BASEDIR=/data/data/com.termux/files/data

while [ 1 ]
do
  REDIS_HOST=localhost FLOWER_ADDRESS=localhost FLOWER_PORT=5556 NODE_ENV=/data/data/com.termux/files/data node index.js
  sleep 20
done


