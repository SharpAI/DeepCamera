# -*- coding: UTF-8 -*-
import os,sys
SRCDIR = os.path.join(os.getenv('RUNTIME_BASEDIR',os.path.abspath(os.path.join(os.path.dirname(__file__), '../'))))
sys.path.append(SRCDIR)

import requests
import numpy as np

from faces.save_embedding import download_img_for_svm, down_embedding, \
    get_embedding_path, get_image_path, create_embedding_string
from qiniuUpload import qiniu_upload_data, SUFFIX
from uploadFile import useAliyun
from aliyunUpload import aliyun_upload_data
from getDeviceInfo import get_current_groupid, get_deviceid

from urllib2 import Request, urlopen, URLError, HTTPError
import json

from flask import Flask
from migrate_db import People, db
import FaceProcessing
from scipy import misc
import facenet
import subprocess

SVM_TRAIN_WITHOUT_CATEGORY=True

uuid = get_deviceid()

BASEDIR = os.getenv('RUNTIME_BASEDIR',os.path.abspath(os.path.join(os.path.dirname(__file__),'../')))
UPLOAD_FOLDER = os.path.join(BASEDIR, 'image')
DATABASE = 'sqlite:///' + os.path.join(BASEDIR, 'data/data.sqlite')
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
db.init_app(app)

facenet_model = os.path.join(BASEDIR, 'facenet_models/20170512-110547/20170512-110547.pb')
sess, graph = FaceProcessing.InitialFaceProcessor(facenet_model)

SVM_TRAIN_WITHOUT_CATEGORY=True

uuid = get_deviceid()

def featureCalculation(imgpath):
    img = misc.imread(os.path.expanduser(imgpath))
    img_size = np.asarray(img.shape)[0:2]
    width = img_size[1]
    height = img_size[0]
    if width != 160 or height != 160:
        print("bad image size")
        return None

    prewhitened = facenet.prewhiten(img)
    with graph.as_default():
        with sess.as_default():
            embedding = FaceProcessing.FaceProcessingImageData(prewhitened, sess, graph)[0]
    return embedding

def txt2embedding(file_path):
    with open(file_path, 'r') as bottleneck_file:
        embedding_string = bottleneck_file.read()
        # print(bottleneck_string)
        embedding_values = [float(x) for x in embedding_string.split(',')]
        embedding = np.array(embedding_values, dtype='f')
        return embedding


def recover_db(img_url, faceid, embedding, style='front'):
    # 恢复embedding到db
    p = People.query.filter_by(aliyun_url=img_url, group_id=group_id).first()
    if not p:
        people = People(embed=embedding, uuid=uuid, group_id=group_id,
                        objId=faceid, aliyun_url=img_url, classId=faceid, style=style)
        db.session.add(people)
        db.session.commit()
        print("Add people")
        return True
    else:
        print("No need add people")
        return False
    '''
    old_train_set = TrainSet.query.filter_by(url=img_url, group_id=group_id).first()  # 一张图片对应的人是唯一的
    if not old_train_set:
        new_train_set = TrainSet(url=img_url, group_id=group_id, is_or_isnot=True,
                                 device_id='', face_id=face_id, filepath='', drop=False, style=style)
        db.session.add(new_train_set)
        db.session.commit()
    '''


def down_img_embedding(img_url, group_id, face_id, style='front'):
    # 下载图片及embedding
    img_path = get_image_path(img_url, group_id, face_id, style)
    embedding_path = get_embedding_path(img_path)
    embedding_url = img_url + SUFFIX
    if not os.path.exists(img_path):
        download_img_for_svm(img_url, group_id, face_id, style)
    embedding = None
    if not os.path.exists(embedding_path):
        status = down_embedding(embedding_url, embedding_path)
        if not status:
            # 下载embedding失败， 开始计算embedding
            embedding = featureCalculation(img_path)
            if embedding is None:
                return False, None
            create_embedding_string(embedding, embedding_path)

            # 上传一次
            key = img_url.rsplit('/', 1)[-1]
            embedding_string = ','.join(str(x) for x in embedding)
            embedding_bytes = embedding_string.encode('utf-8')

            if useAliyun is True:
                url = aliyun_upload_data(key, embedding_bytes)
            else:
                embedding_url = qiniu_upload_data(key, embedding_bytes)

            #print('Download embedding file failed, caculate it.')
        else:
            embedding = txt2embedding(embedding_path)
            #print('Download embedding file suc.')
    else:
        #print('embedding file exist.')
        embedding = txt2embedding(embedding_path)
    # print('need recover db')
    return True, embedding
    #return False, None

def migration():
    sql_db = os.path.join(os.getenv('RUNTIME_BASEDIR',os.path.abspath(os.path.join(os.path.dirname(__file__),'../'))), 'data/') + 'data.sqlite'
    if not os.path.exists(sql_db):
        db.create_all()

    migrate_db_exe = os.path.join(os.getenv('RUNTIME_BASEDIR',os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))) + 'migrate_db.exe'
    migrate_db_py  = os.path.join(os.getenv('RUNTIME_BASEDIR',os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))) + 'migrate_db.py'
    if os.path.exists(migrate_db_exe):
        out_put = subprocess.check_output([migrate_db_exe, 'db', 'upgrade'])
    else:
        out_put = subprocess.check_output(['python', migrate_db_py, 'db', 'upgrade'])
    print(out_put)
    print('> finish migrate upgrade')

if __name__ == '__main__':
    group_id = get_current_groupid()
    total_photos = 0
    new_db_photos = 0

    migration()
    #host="http://localhost:3000/restapi/datasync/token/" + str(group_id)
    host = "http://workaihost.tiegushi.com/restapi/datasync/token/" + str(group_id)
    result = None
    try:
        response = urlopen(host, timeout=10)
    except HTTPError as e:
        print('HTTPError: ', e.code)
    except URLError as e:
        print('URLError: ', e.reason)
    except Exception as e:
        print('Error: ', e)
    else:
        # everything is fine
        if 200 == response.getcode():
            result = response.readline()
            #print(result)
            result = json.loads(result)
            for person in result:
                faceId = person.get("faceId")
                urls = person.get("urls")
                print('--> {}'.format(faceId))
                for url in urls:
                    print('        {}'.format(url))
                    with app.app_context():
                        total_photos = total_photos+1
                        # url,faceid 从点圈群相册获取
                        # todo 可以用for循环解析群相册获取的json数据
                        img_url = url['url']
                        faceid = faceId
                        style = url['style']
                        if SVM_TRAIN_WITHOUT_CATEGORY is True:
                            style = 'front'
                        status, embedding = down_img_embedding(img_url, group_id, faceid, style=style)
                        if status:
                            isAdded = recover_db(img_url, faceid, embedding, style=style)
                            if isAdded is True:
                                new_db_photos = new_db_photos+1
            print("total_photos={}, new_db_photos={}".format(total_photos, new_db_photos))
        else:
            print('response code != 200')
