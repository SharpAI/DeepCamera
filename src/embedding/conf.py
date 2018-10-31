# -*- coding: UTF-8 -*-
# run: $gunicorn -c conf.py upload_api:app
import sys
import os
import multiprocessing
sys.path.append(os.path.abspath('upload_api.py'))
sys.path.append('.')
sys.path.append('..')
from upload_api import crons_start

path_of_current_file = os.path.abspath(__file__)
path_of_current_dir = os.path.split(path_of_current_file)[0]

_file_name = os.path.basename(__file__)

bind = '0.0.0.0:5000'
workers = 3
# workers = multiprocessing.cpu_count() * 2 + 1
worker_class = 'sync'
timeout = 100
# debug=True
loglevel = 'debug'
# pidfile = '%s/run/%s.pid' % (path_of_current_dir, _file_name)
errorlog = '%s/logs/%s_error.log' % (path_of_current_dir, _file_name)
accesslog = '%s/logs/%s_access.log' % (path_of_current_dir, _file_name)

def on_starting(server):
    # gunicorn 主进程启动之前的操作
    crons_start()

