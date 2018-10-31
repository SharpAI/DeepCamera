# coding=utf-8
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

#deeepeye
from celery import Celery
from celery import Task
from celery.signals import worker_process_init
from celery.signals import celeryd_after_setup
from celery.concurrency import asynpool

#deeepeye
asynpool.PROC_ALIVE_TIMEOUT = 60.0 #set this long enough
deepeye = Celery('upload_api-v2',
    broker='redis://guest@localhost/0',
    backend='redis://guest@localhost/0')

@worker_process_init.connect()
def setup(sender=None, **kwargs):
    global m
    import detector as m
@deepeye.task
def detect(image_path, trackerid, ts, cameraId):
    result = m.detect(image_path,trackerid, ts, cameraId)

    return result

deepeye.conf.task_routes = {
    'upload_api-v2.detect': {'queue': 'detect'}
}

if __name__ == '__main__':
    deepeye.start()
