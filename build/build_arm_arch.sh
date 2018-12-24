#!/usr/bin/env bash
if [ ! $# -eq 1 ]; then
    echo "usage: ./build_arm.sh /your/build/path"
    exit 1
fi

buildpath=$(realpath $1)

rm -rf build dist runtime_arch
mkdir runtime_arch

pip install -r  ../src/face_detection/requirements.txt
pyinstaller --clean -y face_detector_arm.spec
mv dist/worker runtime_arch/bin
cp -rf ../src/face_detection/model runtime_arch/bin/

pip install -r ../src/embedding/requirements.txt
pyinstaller --clean -y classifier_server.spec
cp ../src/embedding/judgeutil.so_termux_arch-linux_arm dist/classifier/judgeutil.so
mv dist/classifier runtime_arch/bin
