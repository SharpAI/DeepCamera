#!/bin/bash

export FLOWER_WS="ws://127.0.0.1:5555/api/task/events/task-succeeded/"
export UUID_FILE=/data/data/com.termux/files/home/.ro_serialno
export GROUP_ID='/.cacheresource/workaipython/groupid.txt'
export VERSION_FILE='/.cacheresource/version'
export AUTO_UPDATE_FILE='/.cacheresource/workaipython/wtconf/enableWT'
export DOCKER_COMPOSE_YML='/.cacheresource/docker-compose.yml'
export HOST_ADDRESS="workaihost.tiegushi.com"
export HOST_PORT=80
export RUNTIME_DIR='/.cacheresource'
export RESTART_TIMEOUT=20

while true; do
    echo "entering index.js"
    #pushd /.cacheresource/monitor
    #disable watchtower before startup index.js
    #rm -rf ${AUTO_UPDATE_FILE}
    node index.js
    #popd
    echo "exit index.js"
    sleep 30
done
