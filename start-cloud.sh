#!/bin/bash
YML=./docker/docker-compose-apiserver.yml
if [ $1'x' == 'x' ];then
    echo "usage: ./start-cloud.sh start"
else
    case $1 in
        start )                 echo "starting..."
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
        * )                     echo "usage: ./start-cloud.sh start"
                                exit 1
    esac
fi
exit 1
