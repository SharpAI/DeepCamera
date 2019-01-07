#!/usr/bin/env bash
while [ 1 ]
do
  ./bin/minio server ./data/minio/
  sleep 20
done
