import os
import threading
import time
import minio

from minio import Minio
from minio.error import ResponseError

def str2bool(v):
  return v.lower() in ("yes", "true", "t", "1")

AWS_END_POINT = os.getenv('AWS_END_POINT','')
AWS_PORT = os.getenv('AWS_PORT','80')
AWS_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY','')
AWS_SECRET_KEY = os.getenv('AWS_SECRET_KEY','')
AWS_BUCKET = os.getenv('AWS_BUCKET','')
AWS_READABLE_PREFIX = os.getenv('AWS_READABLE_PREFIX','')
AWS_USE_SSL = str2bool(os.getenv('AWS_USE_SSL','true'))

endpoint = AWS_END_POINT+':'+AWS_PORT
urlprefix = AWS_READABLE_PREFIX

mc = Minio(
    endpoint,
    access_key=AWS_ACCESS_KEY,
    secret_key=AWS_SECRET_KEY,
    secure=AWS_USE_SSL,
)

lock = threading.Lock()
def aws_upload_img(key, imgpath, timeout=4):
    if not os.path.exists(imgpath):
        print('ops! this image not found')
        return ''

    if key is None:
        print('ops! key is None')
        return ''

    url = urlprefix + key

    try:
        start = time.time()
        mc.fput_object(AWS_BUCKET, key, imgpath)
        end = time.time()

        print('uploaded ' + imgpath + ' as ' + url)
        os.remove(imgpath)

        global total_time
        global success_count
        lock.acquire()
        success_count += 1
        total_time += (end - start)
        lock.release()
        return url
    except Exception as e:
        print(e)
        print("upload to aws/minio failed")

    global error_count
    lock.acquire()
    error_count += 1
    lock.release()

    return ''
