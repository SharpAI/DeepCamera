#!/usr/bin/env bash

#export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$PREFIX/lib64
export DATA_RUNTIME_FOLDER=`pwd`/model
export DEVICE_GROUP_ID_FILEPATH=/data/data/com.termux/files/home/.groupid.txt
export DEVICE_UUID_FILEPATH=/data/data/com.termux/files/home/.ro_serialno
export RUNTIME_BASEDIR=`pwd`/src/embedding
#export LD_LIBRARY_PATH=/system/lib64:$LD_LIBRARY_PATH:$PREFIX/lib64:/system/vendor/lib64/egl:/system/vendor/lib64

export CLUSTER_REDIS_ADDRESS=localhost
export CLUSTER_REDIS_PORT=6379
export CLUSTER_CONCURRENCY=1
export CELERY_BROKER_URL=redis://localhost/0
export CELERY_RESULT_BACKEND=redis://localhost/0

## Core Logic
export ONE_KNOWN_PERSON_BYPASS_QUEUE_MODE=0
export DEEP_ANALYSIS_MODE=1
export SAMPLING_TO_SAVE_ENERGY_MODE=0
export RESTRICT_RECOGNITON_MODE=1
export MINIMAL_FACE_RESOLUTION=100
export BIGGEST_FACE_ONLY_MODE=0
export UPLOAD_IMAGE_SERVICE_ENABLED=0
export GIF_UPLOADING=1
export REALTIME_STRANGER_SDK_MESSAGE=1
export ENABLE_STATIC_OBJECT_FILTER=false
export CLUSTER_REDIS_ADDRESS=localhost
export CLUSTER_REDIS_PORT=6379
export REDIS_HOST=localhost
export REDIS_ADDRESS=localhost
export FLOWER_ADDRESS=localhost
export FLOWER_PORT=5556
export BROKERHOST='mqtt://localhost'

## Monitor
export FLOWER_WS="ws://127.0.0.1:5556/api/task/events/task-succeeded/"
export UUID_FILE='/data/data/com.termux/files/home/.ro_serialno'
export GROUP_ID='/data/data/com.termux/files/home/.groupid.txt'
export VERSION_FILE='/.cacheresource/version'
export AUTO_UPDATE_FILE='/.cacheresource/workaipython/wtconf/enableWT'
export DOCKER_COMPOSE_YML='/.cacheresource/docker-compose.yml'
export HOST_ADDRESS="workaihost.tiegushi.com"
export HOST_PORT=80
export RUNTIME_DIR='/.cacheresource'
export RESTART_TIMEOUT=20
