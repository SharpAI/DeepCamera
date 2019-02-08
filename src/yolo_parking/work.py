# coding=utf-8
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os
import json

from celery import Celery
from celery.signals import worker_process_init
from celery.concurrency import asynpool
from yolo import Yolo


# deeepeye
asynpool.PROC_ALIVE_TIMEOUT = 60.0  # set this long enough

redis_host = os.getenv("REDIS_HOST", default="localhost")
redis_port = os.getenv("REDIS_PORT", default="6379")

ENABLE_STATIC_OBJECT_FILTER = json.loads(os.getenv("ENABLE_STATIC_OBJECT_FILTER", default="false").lower())

deepeye = Celery('upload_api-v2',
    broker='redis://guest@'+redis_host+':'+redis_port+'/0',
    backend='redis://guest@'+redis_host+':'+redis_port+'/0')


@worker_process_init.connect()
def setup(sender=None, **kwargs):
    global yolo
    yolo = Yolo()

    #warm up
    yolo.get_car_boxes("test3.png")


@deepeye.task
def detect(image_path, trackerid, ts, cameraId):
    result = yolo.detect(image_path)
    return result


deepeye.conf.task_routes = {
    'upload_api-v2.detect': {'queue': 'detect'}
}

if __name__ == '__main__':

    deepeye.start()
