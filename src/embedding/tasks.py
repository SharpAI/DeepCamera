from __future__ import absolute_import
from celery import Celery
from celery import Task
from billiard import current_process

from time import sleep
from celery.signals import worker_process_init
from celery.signals import celeryd_after_setup
from celery.concurrency import asynpool

import os

asynpool.PROC_ALIVE_TIMEOUT = 60.0 #set this long enough

deepeye = Celery()


deepeye.count = 1
def getQueueName():
    return os.environ['WORKER_TYPE']
@worker_process_init.connect()
def setup(sender=None, **kwargs):
    print('initializing {}'.format(getQueueName()))
    sleep(20)
    # setup
    print('done initializing <<< ==== be called Per Fork/Process')


class FaceDetectorTask(Task):
    def __init__(self):
        print('initializing face detector, load module <<< ==== be called Per Worker')
        self._model = 'testing'
    def detector(self):
        return self._model

@deepeye.task(base=FaceDetectorTask)
def detect(x, y):
    sleep(10)  # Simulate work
    return x + y

@deepeye.task
def extract(x, y):
    sleep(3000)  # Simulate work
    return x -  y

@deepeye.task
def fullimage(x, y):
    sleep(30)  # Simulate work
    return x -  y
