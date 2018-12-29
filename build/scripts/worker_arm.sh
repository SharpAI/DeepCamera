#!/usr/bin/env bash
cd bin
while [ 1 ]
do
  $PREFIX/bin/bash /data/data/com.termux/files/home/arch/startarch c "cd /data/data/com.termux/files/home/runtime_arch/bin && DEEP_ANALYSIS_MODE=0 SAMPLING_TO_SAVE_ENERGY_MODE=1 RESTRICT_RECOGNITON_MODE=1 MINIMAL_FACE_RESOLUTION=200 BIGGEST_FACE_ONLY_MODE=0 UPLOAD_IMAGE_SERVICE_ENABLED=0 GIF_UPLOADING=0 REALTIME_STRANGER_SDK_MESSAGE=1 ENABLE_STATIC_OBJECT_FILTER=true ./worker worker --loglevel INFO -E -n detect -c 1 -Q detect"
  sleep 20
done
