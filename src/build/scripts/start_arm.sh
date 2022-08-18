#!/usr/bin/env bash
function checkUUID()
{
    IFNAME="eth0"
    UUIDFILE=/data/data/com.termux/files/home/.ro_serialno
    GROUPFILE=/data/data/com.termux/files/home/.groupid.txt
    MAC=''
    if [ -e ${UUIDFILE} ];then
        MAC=$(cat ${UUIDFILE})

        if [ $MAC'x' == 'x' ] || [ ${#MAC} != 12 ];then
            #不合法重新生成
            MAC=''
        else
            #使用之前保存到文件的
            echo ${MAC}
        fi
    fi

    #get a uuid ######################################
    if [ 'x'${MAC} == 'x' ]; then
        MAC=$(cat /sys/class/net/${IFNAME}/address | sed 's/://g')
        if [ $MAC'x' == 'x' ] || [ ${#MAC} != 12 ];then
            str1=$RANDOM
            str2=$RANDOM
            MAC='rd'$str1$str2
            touch $UUIDFILE
            echo $MAC > $UUIDFILE
        else
            touch $UUIDFILE
            echo $MAC > $UUIDFILE
        fi
    fi
}

function startserver()
{
    cd /data/data/com.termux/files/home/runtime

    if [ $(ps aux | grep \[r]edis-server | wc -l) -eq 0 ]; then
        redis-server --maxmemory 80mb --maxmemory-policy allkeys-lru --save "" --appendonly no --dbfilename "" --protected-mode no --bind 0.0.0.0 &
    fi

    if [ $(ps aux | grep \[m]osquitto | wc -l) -eq 0 ]; then
        mosquitto &
    fi

    if [ $(ps aux | grep \[m]inio_arm.sh | wc -l) -eq 0 ]; then
        $PREFIX/bin/bash ./minio_arm.sh &
    fi
    if [ $(ps aux | grep \[f]lower_arm.sh | wc -l) -eq 0 ]; then
        $PREFIX/bin/bash ./flower_arm.sh &
    fi
    if [ $(ps aux | grep \[e]mbedding_arm.sh | wc -l) -eq 0 ]; then
        $PREFIX/bin/bash ./embedding_arm.sh &
    fi
    if [ $(ps aux | grep \[w]orker_arm.sh | wc -l) -eq 0 ]; then
        $PREFIX/bin/bash ./worker_arm.sh &
    fi
    if [ $(ps aux | grep \[c]lassifier_worker_arm.sh | wc -l) -eq 0 ]; then
        $PREFIX/bin/bash ./classifier_worker_arm.sh &
    fi
    if [ $(ps aux | grep \[c]lassifier_restserver_arm.sh | wc -l) -eq 0 ]; then
        $PREFIX/bin/bash ./classifier_restserver_arm.sh &
    fi
    if [ $(ps aux | grep \[p]aram_arm.sh | wc -l) -eq 0 ]; then
        $PREFIX/bin/bash ./param_arm.sh &
    fi
    if [ $(ps aux | grep \[s]tart_detector.sh | wc -l) -eq 0 ]; then
        $PREFIX/bin/bash ./start_detector.sh &
    fi
    if [ $(ps aux | grep \[s]tart_monitor.sh | wc -l) -eq 0 ]; then
        $PREFIX/bin/bash ./start_monitor.sh &
    fi

    if [ $(ps aux | grep \[f]aceboxsdk_arm.sh | wc -l) -eq 0 ]; then
        $PREFIX/bin/bash ./faceboxsdk_arm.sh &
    fi
}

#checkUUID
startserver
