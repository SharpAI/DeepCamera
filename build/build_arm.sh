#!/usr/bin/env bash
if [ ! $# -eq 1 ]; then
    echo "usage: ./build_arm.sh /your/build/path"
    exit 1
fi

BUILDWITHSDK='false'

buildpath=$(realpath $1)
runtime=${buildpath}"/runtime"
archruntime=${buildpath}"/runtime_arch"
facebox_sdk_path=${buildpath}"/facebox_sdk"

rm -rf build dist $runtime $archruntime
rm -rf .termux/
rm -rf .minio/
rm -rf .ro_serialno
rm -rf .groupid.txt
rm -rf sharpai-app.tgz

mkdir -p $runtime/bin

if [ ! -d ../model ] || [ ! -f ../model/net2 ] || [ ! -f ../model/net2.params ] || [ ! -f ../model/net2.tar ]; then
    echo "not found model"
    exit
fi
if [ -f ../model/net2.tar.so ];then
    rm -rf ../model/net2.tar.so
fi

if [ ${BUILDWITHSDK}'x' == 'truex' ]; then
    rm -rf ${facebox_sdk_path}
    git clone https://github.com/SharpAI/facebox_sdk facebox_sdk
    pushd facebox_sdk
    git checkout origin/switch_control -b switch_control
    popd

    pip install -r ${facebox_sdk_path}/python/requirements.txt
    pyinstaller --clean facebox_sdk_arm.spec
    cp -r  dist/facebox_sdk_main/ $runtime/bin
    rm -rf dist/facebox_sdk_main/
fi

cp patchs/function.py /data/data/com.termux/files/usr/lib/python2.7/site-packages/tvm-0.5.dev0-py2.7-linux-armv7l.egg/tvm/_ffi/_ctypes/function.py
cp patchs/ndarray.py /data/data/com.termux/files/usr/lib/python2.7/site-packages/tvm-0.5.dev0-py2.7-linux-armv7l.egg/tvm/_ffi/_ctypes/ndarray.py
LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/system/lib:/system/vendor/lib/egl LD_PRELOAD=libatomic.so:libcutils.so pyinstaller --clean -y embedding_arm.spec

cp -rf dist/embedding/* $runtime/bin
rm -rf dist/embedding

pyinstaller --clean parameter_server.spec
cp -rf dist/param/* $runtime/bin/
rm -rf dist/param

pip install -r ../src/flower/requirements.txt
pyinstaller --clean flower_main.spec
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

pushd ${runtime}"/bin"
    wget https://dl.minio.io/server/minio/release/linux-arm/minio
    if [ $? != 0 ]; then
        echo "download minio failed!"
	exit 1
    fi
    chmod a+rx minio
    mkdir -p ${runtime}"/data/minio"
popd

bash ./build_detector.sh ${buildpath}
bash ./build_monitor.sh  ${buildpath}


#build for arch-linux
$PREFIX/bin/bash /data/data/com.termux/files/home/arch/startarch c "cd /data/data/com.termux/files/home/sharpai/build && ./build_arm_arch.sh ."

#generate sharpai.tgz for apk
mkdir -p .termux/boot/
mkdir .minio
touch .ro_serialno
touch .groupid.txt

cp ../src/minio/config.json .minio/
cp scripts/termux_boot_sharpai_arm.sh .termux/boot/
chmod a+rx .termux/boot/termux_boot_sharpai_arm.sh

echo "creating sharpai-app.tgz ..."
tar -czmf sharpai-app.tgz .minio .ro_serialno .groupid.txt .termux runtime runtime_arch
ls -lh sharpai-app.tgz
