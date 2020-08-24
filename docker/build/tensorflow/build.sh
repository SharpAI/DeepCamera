#!/bin/bash
./download.sh
docker build -f Dockerfile -t shareai/tensorflow:armv7l_tf1.8 .
