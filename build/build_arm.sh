#!/usr/bin/env bash

runtime="$1/./runtime"

rm -rf build dist $runtime/bin

mkdir $runtime
cp patchs/function.py /data/data/com.termux/files/usr/lib/python2.7/site-packages/tvm-0.5.dev0-py2.7-linux-armv7l.egg/tvm/_ffi/_ctypes/function.py
cp patchs/ndarray.py /data/data/com.termux/files/usr/lib/python2.7/site-packages/tvm-0.5.dev0-py2.7-linux-armv7l.egg/tvm/_ffi/_ctypes/ndarray.py
LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/system/lib:/system/vendor/lib/egl LD_PRELOAD=libatomic.so:libcutils.so pyinstaller -y embedding_arm.spec

mv dist/embedding $runtime/bin
rm -rf dist/embedding

pyinstaller parameter_server.spec
cp -rf dist/param/* $runtime/bin/
rm -rf dist/param

pyinstaller flower_main.spec
cp -rf dist/flower_main/* $runtime/bin/
rm -rf dist/flower_main

mkdir -p $runtime/data/faces
mkdir -p $runtime/faces/default_data
mkdir -p $runtime/image
cp ../src/embedding/data/data.sqlite $runtime/data/
cp ../src/embedding/data/params.ini $runtime/data/
cp ../src/embedding/faces/default_data/default_face.png $runtime/faces/default_data/
cp ../src/embedding/image/Mike*.png $runtime/image
cp -rf ../src/embedding/pages $runtime/
cp -rf ../src/embedding/migrations $runtime/

cp -rf ../model $runtime/

cp scripts/*_arm.sh $runtime/
chmod +x $runtime/*.sh

bash ./build_detector.sh $1
