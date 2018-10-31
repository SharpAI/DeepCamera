#!/bin/bash

while true; do
	echo "entering index.js"
	node index.js
	echo "exit index.js"
	sleep 1
done

#export FLOWER_WS="ws://127.0.0.1:5555/api/task/events/task-succeeded/"
#export UUID_FILE='/.cacheresource/workaipython/ro_serialno'
#export GROUP_ID='/.cacheresource/workaipython/groupid.txt'
#export VERSION_FILE='/.cacheresource/version'
#export AUTO_UPDATE_FILE='/.cacheresource/workaipython/wtconf/enableWT'
#export HOST_ADDRESS="workaihost.tiegushi.com"
#export HOST_PORT=80
#while true; do
#	echo "entering index.js"
#       rm -rf ${AUTO_UPDATE_FILE}
#	node index.js
#	echo "exit index.js"
#	sleep 1
#done
