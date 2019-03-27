#!/usr/bin/env bash
cpwd=$(pwd)
while [ 1 ]
do
  $PREFIX/bin/bash /data/data/com.termux/files/home/arch/startarch c "cd "${cpwd}" && REDIS_HOST=localhost REDIS_PORT=6379 ONE_KNOWN_PERSON_BYPASS_QUEUE_MODE=0 DEEP_ANALYSIS_MODE=1 SAMPLING_TO_SAVE_ENERGY_MODE=0 RESTRICT_RECOGNITON_MODE=0 MINIMAL_FACE_RESOLUTION=100 BIGGEST_FACE_ONLY_MODE=0 UPLOAD_IMAGE_SERVICE_ENABLED=1 GIF_UPLOADING=1 REALTIME_STRANGER_SDK_MESSAGE=1 ENABLE_STATIC_OBJECT_FILTER=true python worker.py worker --loglevel INFO -E -n detect -c 1 -Q detect"
  sleep 20
done
