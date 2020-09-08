#!/bin/bash

cd tensorflow
./build_x86.sh
cd ../od
./build_x86.sh
cd ../
docker-compose -f docker-compose-x86.yml build
