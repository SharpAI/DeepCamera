#!/bin/bash
ARCH=$(uname -m)
ARCH_NAME="arm"
CPWD=$(pwd)

if [ ${ARCH}'x' == 'aarch64x' ];then
    ARCH_NAME="arm64"
elif [ ${ARCH}'x' == 'armx' ];then
    ARCH_NAME="arm"
elif [ ${ARCH}'x' == 'armv7lx' ];then
    ARCH_NAME="arm"
else
    echo "minio not started"
    exit 1
fi

MINIO_BIN="minio_"${ARCH_NAME}
if [ ! -f ${MINIO_BIN} ]; then
    rm -rf minio
    wget https://dl.minio.io/server/minio/release/linux-${ARCH_NAME}/minio
    mv minio ${MINIO_BIN}
    chmod a+rx ${MINIO_BIN}
fi

${CPWD}/${MINIO_BIN} server ${CPWD} --config-dir=${CPWD}
