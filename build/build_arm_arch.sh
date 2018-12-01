#!/usr/bin/env bash

runtime_tar=$1/./runtime_arch.tar

rm -rf build dist runtime_arch
mkdir runtime_arch

pyinstaller -y face_detector_arm.spec
mv dist/worker runtime_arch/bin
cp -rf ../src/face_detection/model runtime_arch/bin/

rm $runtime_tar
tar -cf $runtime_tar runtime_arch

rm -rf runtime_arch/bin

pyinstaller -y classifier_server.spec
mv dist/classifier runtime_arch/bin

tar -uf $runtime_tar runtime_arch

echo "$runtime_tar is ready"
