export FLOWER_WS="ws://127.0.0.1:5555/api/task/events/task-succeeded/"
export UUID_FILE='../workaipython/ro_serialno'
export GROUP_ID='../workaipython/groupid.txt'
export VERSION_FILE='../version'
export AUTO_UPDATE_FILE='../workaipython/wtconf/enableWT'
export DOCKER_COMPOSE_YML='../docker-compose-prebuilt.yml'
export HOST_ADDRESS="workaihost.tiegushi.com"
export HOST_PORT=80
export RUNTIME_DIR='../'
export DOCKER_COMPOSE_YML_FILENAME='docker-compose-prebuilt.yml'
export RESTART_TIMEOUT=5

while true; do
    echo "entering index.js"
    node index.js
    echo "exit index.js"
    sleep 3
done
