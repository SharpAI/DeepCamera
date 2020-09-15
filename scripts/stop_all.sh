#!/bin/bash

#echo Please reconnect after this script

#ps aux  |  grep -i start_  |  awk '{print $1}' | xargs echo kill -9


stop () {
  echo "to stop $1"
  ps aux  |  grep -i $1  |  awk '{print $1}' | xargs kill -9
}


stopAll () {
  stop start_
  stop redis-server
  stop mosquitto
  stop minio
  stop node
  stop python2
  stop flower_main
  stop embedding
  stop worker
  stop classifier
  stop param
}

stopAll
sleep 4
stopAll
sleep 1

ps aux
