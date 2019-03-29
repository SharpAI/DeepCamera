#!/bin/bash
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$PREFIX/lib:/system/vendor/lib/egl
export LD_PRELOAD=$LD_PRELOAD:../../model/yolo/libdarknet.so:libatomic.so:libcutils.so

cp -a _convert.so_arm32_termux _convert.so
while [ 1 ]
do
    REDIS_HOST=localhost REDIS_PORT=6379 python2 work.py worker --loglevel INFO -E -n detect -c 1 -Q detect
    sleep 20
done

