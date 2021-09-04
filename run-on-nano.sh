#!/bin/bash
#set -x

IFNAME="eth0"
DEVICE_UUID=$MAC
function gen_ro_serial()
{
    UUIDFILE=./docker/workaipython/ro_serialno
    MAC=''
    if [ -e ${UUIDFILE} ];then
        MAC=$(cat ${UUIDFILE})

        if [ $MAC'x' == 'x' ] || [ ${#MAC} != 12 ];then
            MAC=''
        else
            echo ${MAC}
        fi
    fi

    #get a uuid ######################################
    if [ 'x'${MAC} = 'x' ]; then
        MAC=$(ifconfig eth0 | awk '/ether/{print $2}' | tr -d ':' )
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

YML=./docker/docker-compose-nano.yml
if [ $1'x' == 'x' ];then
    echo "usage: ./run-on-nano.sh start"
else
    case $1 in
        start )                 echo "starting..."
                                #docker-compose -f $YML stop
                                #docker-compose -f $YML up -d
                                gen_ro_serial
                                echo "Your Device UUID is echo $MAC"
                                sleep 10
                                docker-compose -f $YML stop
                                docker-compose -f $YML up
                                exit 0
                                ;;
        stop )                  echo "stopping..."
                                docker-compose -f $YML stop
                                exit 0
                                ;;
        reload )                echo "reloading..."
                                docker-compose -f $YML stop
                                docker-compose -f $YML up -d
                                exit 0
                                ;;
        * )                     echo "usage: ./run-on-arm64v8.sh start"
                                exit 1
    esac
fi
exit 1
