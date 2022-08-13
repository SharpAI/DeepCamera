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
from scipy import misc
from face_filter import FaceFilterClass
import time

#deeepeye
asynpool.PROC_ALIVE_TIMEOUT = 60.0 #set this long enough
deepeye = Celery('upload_api-v2',
    broker='redis://guest@redis/0',
    backend='redis://guest@redis/0')

@worker_process_init.connect()
def setup(sender=None, **kwargs):
    global m
    import detector as m
    global face_filter
    face_filter = FaceFilterClass()
@deepeye.task
def detect(image_path, trackerid, ts, cameraId):
    img = misc.imread(image_path)
    result, resized_img = face_filter.resize_image(img, 480)
    if result is not None:
        print("Resize image error!")
        return
    star_time = time.time()
    result, rects, min_value, max_value = face_filter.motion_detect(cameraId, resized_img)
    end_time = time.time()
    print('Performance: motion_detect is {}S'.format(end_time-star_time))
    face_filter.save_static_image(cameraId, result, image_path, min_value, max_value)
    result = m.detect(image_path,trackerid, ts, cameraId, face_filter)

    return result

deepeye.conf.task_routes = {
    'upload_api-v2.detect': {'queue': 'detect'}
}

if __name__ == '__main__':
    deepeye.start()
