#!/bin/bash
cat /sys/class/net/eth0/address | sed 's/://g' > ~/.ro_serialno
echo -n "" > ~/.groupid.txt

redis-server --maxmemory 20mb --maxmemory-policy allkeys-lru --save "" --appendonly no --dbfilename "" &
mosquitto &

pushd src/minio/
    ./start.sh &
popd

pushd src/yolo_detector
    ./work_arm.sh &
popd

pushd src/embedding_human
    ./start_human_arm.sh &
    ./start_human_classifier_restserver_arm.sh &
    ./start_human_classifier_worker_arm.sh &
popd

pushd src/detector_human
    ./start.sh &
popd


pushd src/flower
    CELERY_BROKER_URL=redis://localhost/0 CELERY_RESULT_BACKEND=redis://localhost/0 python2 flower_main.py --port=5556 &
popd
