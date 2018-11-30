#!/usr/bin/env bash

rm -rf build dist runtime

mkdir runtime
pyinstaller classifier_server.spec
mv dist/classifier runtime/bin

pyinstaller embedding.spec
cp -rf dist/embedding/* runtime/bin/
rm -rf dist/embedding

pyinstaller face_detector.spec
cp -rf dist/worker/* runtime/bin/
rm -rf dist/worker

pyinstaller parameter_server.spec
cp -rf dist/param/* runtime/bin/
rm -rf dist/param

pyinstaller flower_main.spec
cp -rf dist/flower_main/* runtime/bin/
rm -rf dist/flower_main

mkdir -p runtime/data/faces
mkdir -p runtime/faces/default_data
mkdir -p runtime/image
cp ../src/embedding/data/data.sqlite ./runtime/data/
cp ../src/embedding/data/params.ini ./runtime/data/
cp ../src/embedding/faces/default_data/default_face.png ./runtime/faces/default_data/
cp ../src/embedding/image/Mike*.png ./runtime/image
cp -rf ../src/embedding/pages ./runtime/
cp -rf ../src/embedding/migrations ./runtime/

cp -rf ../model ./runtime/
cp -rf ../src/face_detection/model/* ./runtime/bin/model/

cp scripts/*_aarch64.sh runtime/
chmod +x runtime/*.sh


./build_detector.sh $1
