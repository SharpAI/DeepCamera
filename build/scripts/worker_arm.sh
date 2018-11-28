#!/usr/bin/env bash
cd bin
while [ 1 ]
do
  LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$PREFIX/lib LD_PRELOAD=libm.so:libatomic.so:libcutils.so:libpython2.7.so.1.0 ./worker worker --loglevel INFO -E -n detect -c 2 -Q detect
  sleep 20
done
