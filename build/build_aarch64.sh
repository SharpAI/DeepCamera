#!/usr/bin/env bash
if [ ! $# -eq 1 ]; then
    echo "usage: ./build_aarch64.sh /your/build/path"
    exit 1
fi

buildpath=$(realpath $1)
runtime=${buildpath}"/runtime"

rm -rf build dist $runtime
rm -rf .termux/
rm -rf .minio/
rm -rf .ro_serialno
rm -rf .groupid.txt
rm -rf sharpai-app.tgz

if [ ! -d ../model ] || [ ! -f ../model/net2 ] || [ ! -f ../model/net2.params ] || [ ! -f ../model/net2.tar ]; then
    echo "not found model"
    exit
fi
if [ -f ../model/net2.tar.so ];then
    rm -rf ../model/net2.tar.so
fi

mkdir -p $runtime/bin/model

pyinstaller --clean -y classifier_server.spec
cp -rf dist/classifier/* runtime/bin/
rm -rf dist/classifier/*

pyinstaller --clean -y embedding.spec
cp -rf dist/embedding/* runtime/bin/
rm -rf dist/embedding

pyinstaller --clean -y face_detector.spec
cp -rf dist/worker/* runtime/bin/
rm -rf dist/worker

pyinstaller --clean -y parameter_server.spec
cp -rf dist/param/* runtime/bin/
rm -rf dist/param

pyinstaller --clean -y flower_main.spec
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

pushd ${runtime}"/bin"
    wget https://dl.minio.io/server/minio/release/linux-arm64/minio
    if [ $? != 0 ]; then
        echo "download minio failed!"
        exit 1
    fi
    chmod a+rx minio
    mkdir -p ${runtime}"/data/minio"
popd

bash ./build_detector.sh ${buildpath}
bash ./build_monitor.sh  ${buildpath}

#generate sharpai.tgz for apk
mkdir -p .termux/boot/
mkdir .minio
touch .ro_serialno
touch .groupid.txt

cp ../src/minio/config.json .minio/
cp scripts/termux_boot_sharpai_aarch64.sh .termux/boot/
chmod a+rx .termux/boot/termux_boot_sharpai_aarch64.sh

echo "creating sharpai-app.tgz ..."
tar -czmf sharpai-app-aarch64.tgz .minio .ro_serialno .groupid.txt .termux runtime
ls -lh sharpai-app-aarch64.tgz
