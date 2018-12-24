#!/bin/bash

export DEVICE_UUID_FILEPATH=/data/data/com.termux/files/home/.ro_serialno
export DEVICE_GROUP_ID_FILEPATH=/data/data/com.termux/files/home/.groupid.txt

while [ 1 ]
do
  CLUSTER_REDIS_ADDRESS=localhost REDIS_HOST=localhost FLOWER_ADDRESS=localhost FLOWER_PORT=5556 node main.bin.js
  sleep 20
done


