#!/usr/bin/env bash
if [ ! -e bin/facebox_sdk_main ];then
    exit 0
fi

cd bin/facebox_sdk_main
while [ 1 ]
do
  LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$PREFIX/lib LD_PRELOAD=libm.so:libatomic.so:libcutils.so:libpython2.7.so.1.0 tsudo ./facebox_sdk_main
  sleep 20
done
