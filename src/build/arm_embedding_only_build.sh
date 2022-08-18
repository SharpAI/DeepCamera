#!/usr/bin/env bash
rm -rf runtime/bin/*
#rm -rf build/embedding_arm
cp patchs/function.py /data/data/com.termux/files/usr/lib/python2.7/site-packages/tvm-0.5.dev0-py2.7-linux-armv7l.egg/tvm/_ffi/_ctypes/function.py
cp patchs/ndarray.py /data/data/com.termux/files/usr/lib/python2.7/site-packages/tvm-0.5.dev0-py2.7-linux-armv7l.egg/tvm/_ffi/_ctypes/ndarray.py
LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/system/lib:/system/vendor/lib/egl LD_PRELOAD=libatomic.so:libcutils.so pyinstaller -y embedding_arm.spec
mv dist/embedding/* runtime/bin/
cp -rf scripts/*_arm.sh runtime/
