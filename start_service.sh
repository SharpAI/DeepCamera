#!/bin/bash


redis-server &
mosquitto &

cd src/embedding
./start.sh &

cd -
cd src/face_detection
./start.sh &

cd -
cd src/detector
./start.sh &

while [ 1 ]
do
  CELERY_BROKER_URL=redis://localhost/0 CELERY_RESULT_BACKEND=redis://localhost/0 flower --port=5555
  sleep 20
done
