#!/bin/bash

#$PREFIX/bin/bash ./stop_all.sh

source ./env/common.sh

if [ -f /system/vendor/lib64/libOpenCL.so ]
then
  export HAS_OPENCL=true
  echo 'has opencl supporting'
else
  export HAS_OPENCL=false
  echo 'no opencl supporting'
fi

sshd &
redis-server --maxmemory 40mb --maxmemory-policy allkeys-lru --save "" --appendonly no --dbfilename "" &
mosquitto &

cd src/embedding
$PREFIX/bin/bash ./start_android_aarch64.sh &
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
  flower --port=5556 --address=0.0.0.0
  sleep 20
done
