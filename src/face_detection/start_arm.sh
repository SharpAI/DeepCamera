#!/bin/bash

while [ 1 ]
do
  LD_PRELOAD=libm.so:libpython2.7.so:libatomic.so:libcutils.so LD_LIBRARY_PATH=/system/lib:/data/data/com.termux/files/usr/lib:/data/data/com.termux/files/usr/lib python2 worker.py worker --loglevel INFO -E -n detect -c 2 -Q detect
  sleep 20
done
