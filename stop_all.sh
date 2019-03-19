#!/bin/bash

echo Please reconnect after this script

killall -9 redis-server mosquitto minio node python2
killall -9 flower_main embedding worker classifier param
killall -9 bash

