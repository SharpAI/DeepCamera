#!/usr/bin/python
# -*- coding: UTF-8 -*-
# 定时周期任务
import os
from crontab import CronTab

# 当前用户创建任务
my_user_cron = CronTab(user=True)

# 新建任务
path = os.path.join(os.getenv('RUNTIME_BASEDIR',os.path.abspath(os.path.dirname(__file__))), 'qiniu_mkzip.py')
job = my_user_cron.new(command='python {} >> ~/qiniu_mkzip.log'.format(path))

# 执行周期
job.hour.every(24)

# write
my_user_cron.write()

# run
job.enable()

