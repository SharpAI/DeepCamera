#!/bin/bash

while [ 1 ]
do
  LD_LIBRARY_PATH=/data/data/com.termux/files/usr/lib64:/data/data/com.termux/files/usr/lib python2 worker.py worker --loglevel INFO -E -n detect -c 1 -Q detect
  sleep 20
done
