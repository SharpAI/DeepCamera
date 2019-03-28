# -*- coding: utf-8 -*-
# SDK:https://developer.qiniu.com/kodo/sdk/1242/python
import os, json

from qiniu import Auth, set_default, put_file, put_data
from uuid import uuid1
import qiniu.config


# 需要填写你的 Access Key 和 Secret Key
access_key = 'Aq-AfdQq7zWeDeRjmjDLWHwVMZgttNQdo07CDDHf'
secret_key = 'lhLLKYpGhqPB-1xOkUjrBTVWRSQqMpaVC-52XVzI'
# 构建鉴权对象
q = Auth(access_key, secret_key)
# 要上传的空间
bucket_name = 'workai'


def qiniu_upload_img(key, imgpath, timeout=4):
    if not os.path.exists(imgpath):
        print('oops! this image not found')
        return ''

    if key is None:
        print('oops! no  key value')
        return ''

    #url = 'http://onm4mnb4w.bkt.clouddn.com/' + key
    url = 'http://workaiossqn.tiegushi.com/' + key
    localfile = imgpath


    try:
        set_default(connection_timeout=timeout)
        token = q.upload_token(bucket_name, key, 3600)
        ret, info = put_file(token, key, localfile)
        if info.status_code == 200:
            print('uploaded ' + localfile + ' as ' + url)
        else:
            url = ''
    except Exception as e:
        print(e)
        print("upload to qiniu failed")
        # os.remove(imgpath)
        return ''
    else:
        # os.remove(imgpath)
        return url


def qiniu_upload_video(key, local_path):
    localfile = local_path
    url = 'http://workaiossqn.tiegushi.com/' + key
    # 上传策略
    policy = {
        # 'insertOnly': 1,  # 新增模式上传文件
        'deleteAfterDays': 3,
    }

    try:
        # 生成上传 Token，可以指定过期时间等
        token = q.upload_token(bucket_name, key, 3600, policy)
        ret, info = put_file(token, key, localfile)
        if info.status_code == 200:
            print('uploaded ' + localfile + ' as ' + url)
        else:
            url = ''
    except Exception as e:
        print(e)
        print("upload video to qiniu failed")
        # os.remove(localfile)
        return ''
    else:
        # os.remove(localfile)
        return url


SUFFIX = '_embedding'


def qiniu_upload_data(key, data, timeout=4):
    """上传二进制流"""
    if data == '':
        return ''
    key = key + SUFFIX
    # url = 'http://onm4mnb4w.bkt.clouddn.com/' + key
    url = 'http://workaiossqn.tiegushi.com/' + key

    try:
        set_default(connection_timeout=timeout)
        token = q.upload_token(bucket_name, key, 3600)
        ret, info = put_data(token, key, data)
        if info.status_code == 200:
            print('uploaded embedding as ' + url)
        else:
            url = ''
    except Exception as e:
        print(e)
        print("upload to qiniu failed")
        # os.remove(imgpath)
        return ''
    else:
        # os.remove(imgpath)
        return url


#if __name__ == '__main__':
#   img_url = "xxx"
#
#   new_img_url=qiniu_upload_img('./6b7964cc-14fb-11e7-8cfb-0242ac11000a')
#   if (len(new_img_url)) < 1:
#       new_img_url = img_url
#   print(new_img_url)
