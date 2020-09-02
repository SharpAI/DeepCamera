#!/bin/bash

cd tensorflow
./build.sh
cd ../od
./build.sh
docker-compose -f docker-compose.yml build

