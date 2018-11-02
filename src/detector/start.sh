#!/bin/bash

while [ 1 ]
do
  REDIS_HOST=localhost FLOWER_ADDRESS=localhost FLOWER_PORT=5556 node index.js
  sleep 20
done


