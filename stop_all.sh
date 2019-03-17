#!/bin/bash

echo Please reconnect after this script

killall -9 redis-server mosquitto minio flower_main embedding worker classifier node param 
killall -9 bash
