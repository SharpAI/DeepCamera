# -*- coding: UTF-8 -*-
# crontab todo 定时周期任务
"""
打包本地图片目录，上传七牛云，并返回url给workai server
"""
import os, zipfile, shutil
import requests
from export_csv import all_trainset, BASE_FOLDER
from utilslib.qiniuUpload import qiniu_upload_img
from upload_api import TrainSet
from utilslib.getDeviceInfo import get_deviceid
# from upload_api import labeled_img

device_id = get_deviceid()
print('Device_id: {} start upload dataset.zip'.format(device_id))

# 打包目录为zip文件（未压缩）
def make_zip(source_dir, output_filename):
    zipf = zipfile.ZipFile(output_filename, 'w')
    pre_len = len(os.path.dirname(source_dir))
    for parent, dirnames, filenames in os.walk(source_dir):
        for filename in filenames:
            pathfile = os.path.join(parent, filename)
            arcname = pathfile[pre_len:].strip(os.path.sep)     #相对路径
            zipf.write(pathfile, arcname)
    zipf.close()


def upload_and_send(group_id):
    make_zip(BASE_FOLDER, 'dataset.zip')
    shutil.move('dataset.zip', os.path.join(BASE_FOLDER, 'dataset.zip'))

    # 上传
    url = qiniu_upload_img(os.path.join(BASE_FOLDER, 'dataset.zip'), timeout=10)
    print("zip_url: {}".format(url))
    # 返回url给server

    payload = {'value': url, 'group_id': group_id, 'uuid': device_id}
    host = 'http://workaihost.tiegushi.com/restapi/workai-group-dataset'
    req = requests.get(host, params=payload, timeout=10)
    print("Send a request to workai")

    # 清扫
    shutil.rmtree(BASE_FOLDER)


if __name__ == '__main__':
    for row in TrainSet.query.group_by('group_id').all():
        group_id = row.group_id
        print('Current group_id: {}'.format(group_id))
        if group_id:
            dataset = TrainSet.query.filter_by(group_id=group_id, is_or_isnot=True).all()
            all_trainset(dataset=dataset)
            upload_and_send(group_id)
