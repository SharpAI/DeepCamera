#!/bin/bash
source ./env/common.sh

if [ -f /system/vendor/lib64/libOpenCL.so ]
then
  export HAS_OPENCL=1
  echo 'has opencl supporting'
else
  export HAS_OPENCL=0
  echo 'no opencl supporting'
fi

redis-server --maxmemory 40mb --maxmemory-policy allkeys-lru --save "" --appendonly no --dbfilename "" &
mosquitto &

cd src/embedding
./start_android_aarch64.sh &
cd -

cd src/face_detection
./start_android_aarch64.sh &
cd -

cd src/detector
./start_android_aarch64.sh &
cd -

cd src/monitor
./start_android_aarch64.sh &
cd -

while [ 1 ]
do
  flower --port=5556 --address=0.0.0.0
  sleep 20
done
