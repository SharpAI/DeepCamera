#!/bin/bash
set -x

#apt-get install avahi-daemon

IFNAME="eth0"

function gen_ro_serial()
{
    UUIDFILE=./workaipython/ro_serialno
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
    if [ 'x'${MAC} = 'x' ]; then
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


#YML=./docker-compose.yml
YML=./docker-compose-x86.yml
if [ $1'x' == 'x' ];then
    echo "usage: ./run-on-mac.sh start"
else
    case $1 in
        start )                 echo "starting..."
                                gen_ro_serial
                                #docker-compose -f $YML stop
                                #docker-compose -f $YML up -d
                                docker-compose -f $YML stop
                                docker-compose -f $YML up
                                exit 0
                                ;;
        stop )                  echo "stopping..."
                                docker-compose -f $YML stop
                                exit 0
                                ;;
        reload )                gen_ro_serial
                                echo "reloading..."
                                docker-compose -f $YML stop
                                docker-compose -f $YML up -d
                                exit 0
                                ;;
        * )                     echo "usage: ./run-on-mac.sh start"
                                exit 1
    esac
fi
exit 1
