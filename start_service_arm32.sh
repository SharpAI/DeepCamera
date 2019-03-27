#!/bin/bash

export LD_LIBRARY_PATH=$LD_LIBRARY:/system/lib:/system/vendor/lib:/system/vendor/lib/egl:$PREFIX/lib
export LD_PRELOAD=$LD_PRELOAD:libatomic.so:libcutils.so

export UUIDFILE=/data/data/com.termux/files/home/.ro_serialno
export GROUPFILE=/data/data/com.termux/files/home/.groupid.txt

if [ -f /system/vendor/lib/libOpenCL.so ] || [ -f /system/vendor/lib/egl/libGLES_mali.so ]
then
  export HAS_OPENCL=true
  echo 'has opencl supporting'
else
  export HAS_OPENCL=false
  echo 'no opencl supporting'
fi

redis-server --maxmemory 80mb --maxmemory-policy allkeys-lru --save "" --appendonly no --dbfilename "" &
mosquitto &

cd src/embedding
./embedding_arm.sh &
./classifier_worker_arm.sh &
./classifier_restserver_arm.sh &
./param_arm.sh &

#./minio_arm.sh &
cd -
cd src/face_detection
./worker_arm.sh &

cd -
cd src/detector
./start_detector.sh &

cd -
cd src/monitor
./start_monitor.sh &

while [ 1 ]
do
  CELERY_BROKER_URL=redis://localhost/0 CELERY_RESULT_BACKEND=redis://localhost/0 flower --port=5556
  sleep 20
done
