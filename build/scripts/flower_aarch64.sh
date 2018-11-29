#!/usr/bin/env bash
export RUNTIME_BASEDIR=`pwd`
export LD_LIBRARY_PATH=$PREFIX/lib64:$PREFIX/lib
export DATA_RUNTIME_FOLDER=../model
cd bin
while [ 1 ]
do
  CELERY_BROKER_URL=redis://localhost/0 CELERY_RESULT_BACKEND=redis://localhost/0 ./flower_main --port=5556
  sleep 20
done
