#!/bin/bash


redis-server --maxmemory 20mb --maxmemory-policy allkeys-lru --save "" --appendonly no --dbfilename "" &
mosquitto &

cd src/embedding
./start_human.sh &

cd -
cd src/yolo_detector
./work.sh &

cd -
cd src/detector
./start.sh &


CELERY_BROKER_URL=redis://localhost/0 CELERY_RESULT_BACKEND=redis://localhost/0 flower --port=5556&
