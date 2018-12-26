#!/bin/bash
while [ 1 ]
do
  $PREFIX/bin/bash /data/data/com.termux/files/home/arch/startarch c "cd /data/data/com.termux/files/home/runtime_arch/bin && TASKER=restserver REDIS_ADDRESS=localhost ./classifier"
  sleep 20
done
