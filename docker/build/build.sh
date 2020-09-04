#!/bin/bash

cd tensorflow
./build.sh
cd ../od
./build.sh
cd ../
docker-compose -f docker-compose.yml build

