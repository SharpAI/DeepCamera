#!/usr/bin/env bash

WORKER_BROKER=amqp://rabbitmq WORKER_TYPE=detect celery worker --loglevel INFO -E -n detect -c 1 -Q detect &
WORKER_BROKER=amqp://rabbitmq WORKER_TYPE=embedding celery worker --loglevel INFO -E -n embedding -c 1 -Q embedding &
WORKER_BROKER=amqp://rabbitmq WORKER_TYPE=celery celery flower &

while [ 1 ]
do
    sleep 2
done
