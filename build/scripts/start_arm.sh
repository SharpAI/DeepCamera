#!/usr/bin/env bash

cd /data/data/com.termux/files/home/runtime
redis-server --maxmemory 80mb --maxmemory-policy allkeys-lru --save "" --appendonly no --dbfilename "" &
mosquitto &

$PREFIX/bin/bash ./minio_arm.sh &
$PREFIX/bin/bash ./flower_arm.sh &
$PREFIX/bin/bash ./embedding_arm.sh &
$PREFIX/bin/bash ./worker_arm.sh &
$PREFIX/bin/bash ./classifier_arm.sh &
$PREFIX/bin/bash ./param_arm.sh &
$PREFIX/bin/bash ./start_detector.sh &
