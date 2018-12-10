#!/usr/bin/env bash
cd bin
while [ 1 ]
do
  $PREFIX/bin/bash /data/data/com.termux/files/home/arch/startarch c "cd /data/data/com.termux/files/home/runtime_arch/bin && ./worker worker --loglevel INFO -E -n detect -c 1 -Q detect"
  sleep 20
done
