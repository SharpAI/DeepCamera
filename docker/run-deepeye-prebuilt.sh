#!/bin/bash
set -x

#apt-get install avahi-daemon

IFNAME="eth0"

function start_avahi()
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

    SERVICEFILE=/etc/avahi/services/deepeye.service
    echo '<?xml version="1.0" standalone="no"?><!--*-nxml-*-->'       >  $SERVICEFILE
    echo '<!DOCTYPE service-group SYSTEM "avahi-service.dtd">'        >> $SERVICEFILE
    echo '<service-group>'                                            >> $SERVICEFILE
    echo '  <name replace-wildcards="yes">%h</name>'                  >> $SERVICEFILE
    echo '  <service>'                                                >> $SERVICEFILE
    echo '    <type>_DeepEye._tcp</type>'                             >> $SERVICEFILE
    echo '    <port>8000</port>'                                      >> $SERVICEFILE
    echo '    <txt-record>macAddress='$MAC'</txt-record>'             >> $SERVICEFILE
    echo '    <txt-record>uuid='$MAC'</txt-record>'                   >> $SERVICEFILE
    echo '  </service>'                                               >> $SERVICEFILE
    echo '</service-group>'                                           >> $SERVICEFILE

    CONF="/etc/avahi/avahi-daemon.conf"
    echo "[server]"                          >  ${CONF}
    echo "use-ipv4=yes"                      >> ${CONF}
    echo "use-ipv6=yes"                      >> ${CONF}
    echo "allow-interfaces="${IFNAME}        >> ${CONF}
    echo "ratelimit-interval-usec=1000000"   >> ${CONF}
    echo "ratelimit-burst=1000"              >> ${CONF}
    echo "[wide-area]"                       >> ${CONF}
    echo "enable-wide-area=yes"              >> ${CONF}
    echo "[publish]"                         >> ${CONF}
    echo "publish-hinfo=no"                  >> ${CONF}
    echo "publish-workstation=no"            >> ${CONF}
    echo "[reflector]"                       >> ${CONF}
    echo "[rlimits]"                         >> ${CONF}
    echo "rlimit-core=0"                     >> ${CONF}
    echo "rlimit-data=4194304"               >> ${CONF}
    echo "rlimit-fsize=0"                    >> ${CONF}
    echo "rlimit-nofile=768"                 >> ${CONF}
    echo "rlimit-stack=4194304"              >> ${CONF}
    echo "rlimit-nproc=3"                    >> ${CONF}
}

function start_network()
{
    TARGET_IP='192.168.1.253'
    TARGET_DEV=${IFNAME}

    dev_exist=$(ip addr show $TARGET_DEV':0' | grep $TARGET_IP | wc -l)
    if [ 'xx'$dev_exist == 'xx''0' ]; then
        echo "new one"
    else
        echo "remove and new one"
        ip addr del $TARGET_IP'/24'  dev $TARGET_DEV
    fi
    ip addr add $TARGET_IP'/24' brd + dev $TARGET_DEV label $TARGET_DEV':0'
}

function prepare()
{
    start_avahi
    start_network

    ROOT=$(mount | grep "\/ " | cut -d ' ' -f1)
    DOCKER=$(mount | grep "\/var\/lib\/docker " | cut -d ' ' -f1)
    OS=$(uname -s)
    systemd=$(which systemctl | wc -l)

    if [ ${OS}'x' == "Linux"'x' ]; then
        if [ ${systemd}'x' == '0''x' ];then
            /etc/init.d/avahi-daemon stop
        else
            systemctl restart avahi-daemon.socket
            systemctl restart avahi-daemon
        fi
    fi

    if [ $ROOT'x' != 'x' ];then
        resize2fs $ROOT
    fi
    if [ $DOCKER'x' != 'x' ];then
        resize2fs $DOCKER
    fi
}

#YML=./docker-compose.yml
YML=./docker-compose-prebuilt.yml
if [ $1'x' == 'x' ];then
    echo "usage: ./deepeye.sh start"
else
    case $1 in
        start )                 echo "starting..."
                                prepare
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
        reload )                prepare
                                echo "reloading..."
                                docker-compose -f $YML stop
                                docker-compose -f $YML up -d
                                exit 0
                                ;;
        * )                     echo "usage: ./deepeye.sh start"
                                exit 1
    esac
fi
exit 1
