#!/usr/bin/env bash

redis-server --maxmemory 20mb --maxmemory-policy allkeys-lru --save "" --appendonly no --dbfilename "" &
mosquitto &

./embedding_aarch64.sh &
./worker_aarch64.sh &
./classifier_aarch64.sh &
./param_aarch64.sh
