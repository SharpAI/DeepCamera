#!/bin/bash
source ./env/common.sh

redis-server --maxmemory 40mb --maxmemory-policy allkeys-lru --save "" --appendonly no --dbfilename "" &
mosquitto &

cd src/embedding
$PREFIX/bin/bash ./start_andrid_aarch64.sh &
cd -

cd src/face_detection
$PREFIX/bin/bash ./start_android_aarch64.sh &
cd -

cd src/detector
$PREFIX/bin/bash ./start_android_aarch64.sh &
cd -

cd src/monitor
    $PREFIX/bin/bash ./start_android_aarch64.sh &
cd -

while [ 1 ]
do
  flower --port=5556
  sleep 20
done
