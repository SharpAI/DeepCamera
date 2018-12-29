#!/bin/bash
while [ 1 ]
do
  $PREFIX/bin/bash /data/data/com.termux/files/home/arch/startarch c "cd /data/data/com.termux/files/home/runtime_arch/bin && DEVICE_GROUP_ID_FILEPATH=/data/data/com.termux/files/home/.groupid.txt DEVICE_UUID_FILEPATH=/data/data/com.termux/files/home/.ro_serialno TASKER=restserver REDIS_ADDRESS=localhost RUNTIME_BASEDIR=/data/data/com.termux/files/home/runtime ./classifier"
  sleep 20
done
