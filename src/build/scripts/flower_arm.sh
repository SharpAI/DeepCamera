#!/usr/bin/env bash
cd bin
while [ 1 ]
do
  LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$PREFIX/lib LD_PRELOAD=libm.so:libatomic.so:libcutils.so:libpython2.7.so.1.0 CELERY_BROKER_URL=redis://localhost/0 CELERY_RESULT_BACKEND=redis://localhost/0 ./flower_main --port=5556
  sleep 20
done
