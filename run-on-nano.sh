#!/bin/bash
set -x

IFNAME="eth0"

YML=./docker/docker-compose-arm64v8.yml
if [ $1'x' == 'x' ];then
    echo "usage: ./run-on-arm64v8.sh start"
else
    case $1 in
        start )                 echo "starting..."
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
