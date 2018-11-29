#!/usr/bin/env bash

redis-server --maxmemory 20mb --maxmemory-policy allkeys-lru --save "" --appendonly no --dbfilename "" &
mosquitto &

./flower_arm.sh &
./embedding_arm.sh &
./worker_arm.sh &
./classifier_arm.sh &
./param_arm.sh &
./start_detector.sh &
