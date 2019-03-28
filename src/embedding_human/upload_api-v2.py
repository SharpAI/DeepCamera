# coding=utf-8
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os, json, time, sys, thread, base64
import argparse
import unicodedata
import shutil
import subprocess
import threading
# import dlib
import math
import time
import os.path
import Queue
from threading import Timer
import requests

from collections import defaultdict
from flask import Flask, request, url_for, make_response, abort, Response, jsonify, send_from_directory, redirect
from flask_sqlalchemy import SQLAlchemy
from migrate_db import People, TrainSet, db, AutoGroupSet, Stranger, Frame
from sqlalchemy import exc
#from flask_script import Server, Manager
#from flask_migrate import Migrate, MigrateCommand
#from werkzeug.utils import secure_filename
from uuid import uuid1
import urllib2
from urllib2 import Request, urlopen, URLError, HTTPError

from PIL import Image
#import tensorflow as tf
import numpy as np
from scipy import misc
from math import hypot
from multiprocessing import Process
from collections import OrderedDict

USE_DEFAULT_DATA=True   # Enable to use "groupid_default" for SVM training

import facenet
#import clustering_people
from subprocess import Popen, PIPE

import FaceProcessing
from utilslib.mqttClient import MyMQTTClass
from utilslib.persistentUUID import getUUID
from utilslib.save2gst import save2gst, post2gst_motion, post2gst_video
from utilslib.save2gst import sendMessage2Group
from utilslib.getDeviceInfo import deviceId, get_current_groupid, get_deviceid, save_groupid_to_file, check_groupid_changed
from utilslib.qiniuUpload import qiniu_upload_img, qiniu_upload_video, qiniu_upload_data, SUFFIX
# from utilslib.make_a_gif import load_all_images, build_gif, url_to_image
# from utilslib.timer import Timer
from utilslib.clean_droped_data import clean_droped_embedding

from objects.generate_bottlenecks import resize
from faces import save_embedding
from utilslib.resultqueue import push_resultQueue, get_resultQueue

#deeepeye
from celery import Celery
from celery import Task
from billiard import current_process
from celery.signals import worker_process_init
from celery.signals import celeryd_after_setup
from celery.concurrency import asynpool

BASEDIR = os.getenv('RUNTIME_BASEDIR',os.path.abspath(os.path.dirname(__file__)))
TMP_DIR_PATH = os.path.join(BASEDIR, 'data', 'faces', 'tmp_pic_path')
UPLOAD_FOLDER = os.path.join(BASEDIR, 'image')
DATABASE = 'sqlite:///' + os.path.join(BASEDIR, 'data', 'data.sqlite')
face_tmp_objid = None
obje_tmp_objid = None
EN_OBJECT_DETECTION = False
FACE_DETECTION_WITH_DLIB = False # Disable DLIB at this time
EN_SOFTMAX = False
SOFTMAX_ONLY = False

isUpdatingDataSet = False
webShowFace = False

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif', 'bitmap'])
EXT_IMG='png'

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

# db = SQLAlchemy(app)
db.init_app(app)
ENABLE_DEBUG_LOG_TO_GROUP = False
DO_NOT_UPLOAD_IMAGE = False
DO_NOT_REPORT_TO_SERVER = False
NEAR_FRONTIAL_ONLY = False

image_size = 112
margin = 6
facenet_model = os.path.join(BASEDIR, 'facenet_models/20170512-110547/20170512-110547.pb')
minsize = 50  # minimum size of face
threshold = [0.6, 0.7, 0.7]  # three steps's threshold
factor = 0.709  # scale factor
confident_value = 0.67
mineyedist = 0.3 # Eye distance of width of face bounding box
CONFIDENT_VALUE_THRESHOLD = 0.80 #点圈显示的匹配度阈值，大于这个才显示,针对数据库遍历

FOR_ARLO = True
# BLURY_THREHOLD = 10 # Blur image if less than it. Reference: http://www.pyimagesearch.com/2015/09/07/blur-detection-with-opencv/

uploadImg=None
mqttc=None
gbottlenecks=None
trainfromfottlenecks=None
gFlask_port=None
preFrameOnDevice = {}
all_face_index = 0 #每当识别出一个人脸就+1，当2个人同时出现在图片里面并且都不认识，需要区分开来

#deeepeye
asynpool.PROC_ALIVE_TIMEOUT = 60.0 #set this long enough

CLUSTER_REDIS_ADDRESS = os.getenv('CLUSTER_REDIS_ADDRESS','redis')
CLUSTER_REDIS_PORT = os.getenv('CLUSTER_REDIS_PORT','6379')
deepeye = Celery('upload_api-v2',
    broker='redis://'+CLUSTER_REDIS_ADDRESS+':'+CLUSTER_REDIS_PORT+'/0',
    backend='redis://'+CLUSTER_REDIS_ADDRESS+':'+CLUSTER_REDIS_PORT+'/0')
deepeye.count = 1

# run as worker only
CLUSTER_WORKERONLY = os.getenv('CLUSTER_WORKERONLY', False)

HAS_OPENCL = os.getenv('HAS_OPENCL', 'true')
SAVE_ORIGINAL_FACE = False
original_face_img_path = os.path.join(BASEDIR, 'data', 'original_face_img')
if not os.path.exists(original_face_img_path):
    os.mkdir(original_face_img_path)

SVM_CLASSIFIER_ENABLED=True
SVM_SAVE_TEST_DATASET=True
SVM_TRAIN_WITHOUT_CATEGORY=True
SVM_HIGH_SCORE_WITH_DB_CHECK=True

counter = 0

if HAS_OPENCL == 'false':
    from embedding_client import get_remote_embedding

def featureCalculation(imgpath):
    img = misc.imread(os.path.expanduser(imgpath))
    prewhitened = facenet.prewhiten(img)

    embedding = FaceProcessing.FaceProcessingImageData2(img)
    return embedding

def allowed_file(filename):
    """
    检查文件扩展名是否合法
    :param filename:
    :return: 合法 为 True
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

def insertOneImageIntoPeopleDB(filepath, uuid, group_id, objid, url, notFace=False, style="front"):

    if notFace is True:
        classId = "notface"
    else:
        classId = objid

    if not os.path.exists(filepath):
        print("file not exists %s" %(filepath))
        return
    embedding = featureCalculation2(filepath)
    with app.app_context():
        people = People(embed=embedding, uuid=uuid, group_id=group_id,
                        objId=objid, aliyun_url=url, classId=classId, style=style)
        db.session.add(people)
        db.session.commit()
    os.remove(filepath)
    return embedding


#For AutoGroup
#AutogroupFilesList = {}
#AutogroupDatasetFilesList = {}
AutogroupDB = None
AutogroupDatasetDB = None
isSyncAutogroupDataset = True
isStartAutogroup = False
AUTOGROUP_UNKNOWNFACES_DB =  os.path.join(BASEDIR, 'autogroup_unknownfaces_db.json')
AUTOGROUP_DATASET_DB =  os.path.join(BASEDIR, 'autogroup_dataset_db.json')

class MyDB:
    def __init__(self, dbpath, isSave=False):
        print("MyDB: __init__")
        self.isSave = isSave
        self.collection = {}
        if (os.path.isfile(dbpath)):
            with open(dbpath) as fJson:
                self.collection = json.load(fJson)
            self.dbpath = dbpath

    def fetch(self):
        return self.collection.copy()

    def find(self, key, fields):
        return self.collection.get(key, fields)
        '''
        if key is None:
            return {}
        if key in self.collection.keys():
            if fields is None:
                return self.collection[key]
            subDic = self.collection[key]
            isMatch = True
            for subKey, subValue in fields:
                if subKey not in subDic.keys() or subValue != subDic[subKey]:
                    isMatch = False
                    return {}
            if isMatch is True:
                return subDic
        return {}
        '''

    def insert(self, key, fields):
        self.collection[key] = fields
        if self.isSave is True:
            self.save()

    def update(self, key, fields):
        self.collection.update({key:fields})
        if self.isSave is True:
            self.save()

    def remove(self, key):
        self.collection.pop(key, "Key not Found!")
        if self.isSave is True:
            self.save()

    def batch_insert(self, items):
        print("items={}".format(items))
        for key, value in items.items():
            if isinstance(value,dict):
                self.insert(key, value)
            else:
                print("batch_insert: invalid data format.")
        if self.isSave is True:
            self.save()

    def save(self):
        if self.dbpath is None:
            return
        with open(self.dbpath, 'w') as fJson:
            json.dump(self.collection, fJson)


def AutoGroupSetInsert(obj):
    print("test")

def AutoGroupSetUpdate(obj):
    print("test")

def AutoGroupSetRemove(obj):
    print("test")

def disposeAutoGroupFunc(type, json=None):
    global AutogroupDB
    global AutogroupDatasetDB
    global isSyncAutogroupDataset
    global isStartAutogroup

    print("disposeAutoGroupFunc: type={}, json={}".format(type, json))

    if AutogroupDB is None:
        AutogroupDB = MyDB(AUTOGROUP_UNKNOWNFACES_DB)
    if AutogroupDatasetDB is None:
        AutogroupDatasetDB = MyDB(AUTOGROUP_DATASET_DB)

    if type == "dataset":
        AutogroupDatasetDB.batch_insert(json)
        print("Download autogroup dataset...")
    elif type == "syncdataset":
        isSyncAutogroupDataset = True
        print("Set isSyncAutogroupDataset to True")
    elif type == "autogroup":
        if json is not None:
            AutogroupDB.batch_insert(json)
        isStartAutogroup = True
        print("Autogroup...")

#Path format: GroupID_FaceId/url_filename
def getFacialImagePath(img_path):
    part1 = os.path.basename(os.path.dirname(img_path))
    part2 = os.path.basename(img_path)
    return part1+"/"+part2

def downloadAutogroupDataset(result, group_id):
    failedDownloadedItems = []
    for person in result:
        faceId = person.get("faceId")
        urls = person.get("urls")
        print('--> {}'.format(faceId))
        for url in urls:
            #print('        {}'.format(url))
            # url,faceid 从点圈群相册获取
            # todo 可以用for循环解析群相册获取的json数据
            img_url = url['url']
            faceid = faceId
            style = url['style']

            if style != 'front':
                #print("style=%s"%style);
                continue

            #status, embedding = down_img_embedding(img_url, group_id, faceid, style=style)
            img_path = save_embedding.get_image_path_dst(img_url, group_id, faceId, style, "autogroup")
            #print("img_path = {}".format(img_path))
            embedding_path = save_embedding.get_embedding_path(img_path)
            embedding = None
            if not os.path.exists(img_path):
                img_path = save_embedding.download_img_for_svm_dst(img_url, group_id, faceId, style, "autogroup")
            if img_path:
                if not os.path.exists(embedding_path):
                    img = misc.imread(os.path.expanduser(img_path))  # 手动裁剪后的图片需要再缩放一下
                    aligned = misc.imresize(img, (image_size, image_size), interp='bilinear')
                    misc.imsave(img_path, aligned)
                    embedding = featureCalculation(img_path)
                    embedding_path = save_embedding.get_embedding_path(img_path)
                    save_embedding.create_embedding_string(embedding, embedding_path)
                    #print("1, type(embedding)={}".format(type(embedding)))
                old_autogroup_set = AutoGroupSet.query.filter_by(url=img_url, group_id=group_id, is_or_isnot=True, style=style).first()
                if not old_autogroup_set:
                    if embedding is None:
                        embedding_path = save_embedding.get_embedding_path(img_path)
                        embedding = save_embedding.read_embedding_string(embedding_path)
                        embedding = np.asarray(embedding)
                        print("read_embedding_string...........")
                        print("2, type(embedding)={}".format(type(embedding)))
                    unique_face_id = ''
                    if unique_face_id in url:
                        unique_face_id = url['unique_face_id']
                    #unique_face_id = url['unique_face_id'] if unique_face_id in url else ''
                    autoGroupSet = AutoGroupSet(url=img_url, group_id=group_id, is_or_isnot=True,
                                     device_id='', face_id=faceId, unique_face_id=unique_face_id, style=style, filepath=img_path, embed=embedding)
                    db.session.add(autoGroupSet)
                    db.session.commit()
                    print('-> syncAutogroupDataset downloaded url {} to {}'.format(url['url'], img_path))
            else:
                failedDownloadedItems.append(person)
    return failedDownloadedItems

def syncAutogroupDatasetFunc():
    group_id = get_current_groupid()

    #host="http://localhost:3000/restapi/datasync/token/" + str(group_id)
    host = "http://workaihost.tiegushi.com/restapi/datasync/token/" + str(group_id)
    result = None
    try:
        response = urlopen(host, timeout=10)
    except HTTPError as e:
        print('HTTPError: ', e.code)
        return False
    except URLError as e:
        print('URLError: ', e.reason)
        return False
    except Exception as e:
        print('Error: ', e)
        return False
    else:
        # everything is fine
        if 200 == response.getcode():
            result = response.readline()
            #print(result)
            result = json.loads(result)

            failedDownloadedItems = downloadAutogroupDataset(result, group_id)
            try_count = 0
            while len(failedDownloadedItems) > 0:
                try_count = try_count+1
                print("len(failedDownloadedItems) = {}, try_count={}".format(len(failedDownloadedItems), try_count))
                if try_count > 3:
                    print("We have tried 3 times to download the autogroup dataset.")
                    break
                failedDownloadedItems = downloadAutogroupDataset(failedDownloadedItems, group_id)

            #Remove invalid data from local DB
            urlsInLocalDB = AutoGroupSet.query.filter_by(group_id=group_id, style="front").all()
            urlsOnServer = dict()
            for person in result:
                faceId = person.get("faceId")
                urls = person.get("urls")
                for url in urls:
                    img_url = url['url']
                    faceid = faceId
                    style = url['style']
                    urlsOnServer[img_url] = group_id, faceId, style
            print("len(urlsInLocalDB) = {}".format(len(urlsInLocalDB)))
            print("len(urlsOnServer) = {}".format(len(urlsOnServer)))
            #print("urlsOnServer = {}".format(urlsOnServer))
            if urlsInLocalDB:
                for item in urlsInLocalDB:
                    image_path = None
                    #print("item = {}, item.url={}".format(item, item.url))
                    if item.url not in urlsOnServer.keys():
                        print("{}, {}, {}, {} is not on server, delete it from local DB.".format(item.url, item.group_id, item.face_id, item.style))
                        if item.filepath:
                            image_path = item.filepath
                        db.session.delete(item)
                        db.session.commit()
                        if image_path and os.path.isfile(image_path):
                            print('Remove image from local {}'.format(image_path))
                            os.remove(image_path)
                        embedding_path = save_embedding.get_embedding_path(image_path)
                        if embedding_path and os.path.isfile(embedding_path):
                            print('Remove embedding from local {}:'.format(embedding_path))
                            os.remove(embedding_path)
            #Remove invalid photos from local
            '''
            dataset = []
            for path in paths.split(':'):
                path_exp = os.path.expanduser(path)
                classes = [path for path in os.listdir(path_exp) \
                                if os.path.isdir(os.path.join(path_exp, path))]
                classes.sort()
                nrof_classes = len(classes)
                for i in range(nrof_classes):
                    class_name = classes[i]
                    facedir = os.path.join(path_exp, class_name)
                    image_paths = []
                    if os.path.isdir(facedir):
                        images = os.listdir(facedir)
                        for img in images:
                            dataset.append(os.path.join(facedir,img))
            if len(dataset) > 0:
                for image_path in dataset:
                    l5 = (item for item in urlsInLocalDB if item.filepath == image_path)
                    if not l5:
                        print("image_path({}) only in local.".format(image_path))
                        if image_path and os.path.exists(image_path):
                            os.remove(filepath)
                        embedding_path = save_embedding.get_embedding_path(image_path)
                        if embedding_path and os.path.isfile(embedding_path):
                            os.remove(embedding_path)
            '''
            return True
        else:
            print('response code != 200')
            return False

#Sync train data sets
def recover_db(img_url, group_id, faceid, filepath, embedding, style='front'):
    # 恢复embedding到db
    uuid = get_deviceid()
    p = People.query.filter_by(aliyun_url=img_url, group_id=group_id).first()
    if not p:
        people = People(embed=embedding, uuid=uuid, group_id=group_id,
                        objId=faceid, aliyun_url=img_url, classId=faceid, style=style)
        db.session.add(people)
        db.session.commit()
        print("Add people")
        #return True
    #else:
        #print("No need add people")
        #return False

    old_train_set = TrainSet.query.filter_by(url=img_url, group_id=group_id).first()  # 一张图片对应的人是唯一的
    if not old_train_set:
        new_train_set = TrainSet(url=img_url, group_id=group_id, is_or_isnot=True,
                                 device_id='', face_id=faceid, filepath=filepath, drop=False, style=style)
        db.session.add(new_train_set)
        db.session.commit()
    else:
        if old_train_set.filepath != filepath:
            print("Update filepath in local DB")
            TrainSet.query.filter_by(url=img_url, group_id=group_id).update(dict(filepath=filepath))
            db.session.commit()

def check_image_valid(filepath):
    if filepath is None:
        return False
    if not os.path.exists(filepath):
        print("not found {}".format(filepath))
        return False
    if os.path.getsize(filepath) < 1:
        print("invalid file size {}".format(filepath))
        return False
    return True

def downloadTrainDatasets(result, group_id):
    failedDownloadedItems = []
    img_path = None
    embedding_path = None
    try:
        for person in result:
            faceId = person.get("faceId")
            urls = person.get("urls")
            print('--> {}'.format(faceId))
            for url in urls:
                #print('        {}'.format(url))
                # url,faceid 从点圈群相册获取
                # todo 可以用for循环解析群相册获取的json数据
                img_url = url['url']
                faceid = faceId
                style = url['style']

                if SVM_TRAIN_WITHOUT_CATEGORY is True:
                    style = 'front'
                else:
                    if style == 'left_side' or style == 'right_side' or style == 'lower_head' or style == 'blury':
                        continue
                    else:
                        style = 'front'
                #status, embedding = down_img_embedding(img_url, group_id, faceid, style=style)
                print('img_url: ', img_url)
                img_path = save_embedding.get_image_path(img_url, group_id, faceId, style)
                print("img_path = {}".format(img_path))
                embedding_path = save_embedding.get_embedding_path(img_path)
                print("embedding_path = {}".format(embedding_path))
                denoise_path = save_embedding.get_image_denoise_path(img_path)
                recreate_embedding = False
                embedding = None
                if not os.path.exists(img_path):
                    print('img-path not exists ----- ')
                    img_path = save_embedding.download_img_for_svm(img_url, group_id, faceId, style)
                if img_path and check_image_valid(img_path):
                    if not os.path.exists(denoise_path):
                        img = misc.imread(os.path.expanduser(img_path))
                        save_embedding.save_image_denoise(img, denoise_path)
                        recreate_embedding = True

                    if os.path.exists(denoise_path) is True and check_image_valid(denoise_path) is False:
                        os.remove(embedding_path)
                        os.remove(denoise_path)
                        recreate_embedding = False
                        continue

                    if not os.path.exists(embedding_path) or recreate_embedding == True:
                        img = misc.imread(os.path.expanduser(denoise_path))  # 手动裁剪后的图片需要再缩放一下
                        aligned = misc.imresize(img, (image_size, image_size), interp='bilinear')
                        misc.imsave(img_path, aligned)
                        print('......')
                        print('img_path: ',img_path)
                        embedding = featureCalculation2(img_path)
                        print('----------')
                        #embedding = featureCalculation(img_path)
                        embedding_path = save_embedding.get_embedding_path(img_path)
                        save_embedding.create_embedding_string(embedding, embedding_path)
                        #print("1, type(embedding)={}".format(type(embedding)))
                    else:
                        embedding_path = save_embedding.get_embedding_path(img_path)
                        embedding = save_embedding.read_embedding_string(embedding_path)
                        embedding = np.asarray(embedding)
                    recover_db(img_url, group_id, faceid, img_path, embedding, style=style)
                    #print('-> downloadTrainDatasets downloaded url {} to {}'.format(url['url'], img_path))
                else:
                    if img_path is not None and os.path.exists(img_path):
                        os.remove(img_path)
                    failedDownloadedItems.append(person)
    except Exception as ex:
        print('downloadTrainDatasets: except:', ex)
        if img_path and os.path.isfile(img_path):
            print('downloadTrainDatasets: Remove image from local {}'.format(img_path))
            os.remove(img_path)
        if embedding_path and os.path.isfile(embedding_path):
            print('downloadTrainDatasets: Remove embedding from local {}'.format(embedding_path))
            os.remove(embedding_path)
    return failedDownloadedItems

def disposeFinalSyncDatasetsThreadFunc(device_id, toid):
    invalid_images_onserver = 0
    try:
        group_id = get_current_groupid()
        #host="http://localhost:3000/restapi/datasync/token/" + str(group_id)
        host = "http://workaihost.tiegushi.com/restapi/datasync/token/" + str(group_id)
        result = None
        try:
            response = urlopen(host, timeout=10)
        except HTTPError as e:
            print('HTTPError: ', e.code)
            return False
        except URLError as e:
            print('URLError: ', e.reason)
            return False
        except Exception as e:
            print('Error: ', e)
            return False
        else:
            # everything is fine
            if 200 == response.getcode():
                result = response.readline()
                #print(result)
                result = json.loads(result)

                failedDownloadedItems = downloadTrainDatasets(result, group_id)
                try_count = 0
                while len(failedDownloadedItems) > 0:
                    try_count = try_count+1
                    print("len(failedDownloadedItems) = {}, try_count={}".format(len(failedDownloadedItems), try_count))
                    if try_count > 3:
                        print("We have tried 3 times to download the training dataset.")
                        break
                    failedDownloadedItems = downloadTrainDatasets(failedDownloadedItems, group_id)

                #Remove invalid data from local DB
                urlsInLocalDB = TrainSet.query.filter_by(group_id=group_id).all()
                urlsOnServer = dict()
                for person in result:
                    faceId = person.get("faceId")
                    urls = person.get("urls")
                    for url in urls:
                        img_url = url['url']
                        faceid = faceId
                        style = url['style']
                        if style == 'left_side' or style == 'right_side' or style == 'lower_head' or style == 'blury':
                            invalid_images_onserver += 1
                            continue
                        urlsOnServer[img_url] = group_id, faceId, style
                print("Trainsets: len(urlsInLocalDB) = {}".format(len(urlsInLocalDB)))
                print("Trainsets: len(urlsOnServer) = {}".format(len(urlsOnServer)))
                urlsTemp = {}
                deleteUrlsInLocalDB = []
                if urlsInLocalDB:
                    for item in urlsInLocalDB:
                        image_path = None
                        #print("item = {}, item.url={}".format(item, item.url))
                        if (item.url in urlsTemp and urlsTemp[item.url] == 1) or item.url not in urlsOnServer.keys():
                            print("{}, {}, {}, {} is not on server, delete it from local DB.".format(item.url, item.group_id, item.face_id, item.style))
                            deleteUrlsInLocalDB.append(item)
                            if item.filepath:
                                image_path = item.filepath
                            db.session.delete(item)
                            db.session.commit()
                            if image_path and os.path.isfile(image_path):
                                print('Remove image from local {}'.format(image_path))
                                os.remove(image_path)
                            embedding_path = save_embedding.get_embedding_path(image_path)
                            if embedding_path and os.path.isfile(embedding_path):
                                print('Remove embedding from local {}:'.format(embedding_path))
                                os.remove(embedding_path)
                        urlsTemp[item.url] = 1
                    if len(deleteUrlsInLocalDB) > 0:
                        for item in deleteUrlsInLocalDB:
                            urlsInLocalDB.remove(item)
                urlsTemp = None
                print("Trainsets: 2, len(urlsInLocalDB) = {}".format(len(urlsInLocalDB)))
                print("Trainsets: 2, len(urlsOnServer) = {}".format(len(urlsOnServer)))

                #Remove invalid photos from local
                dataset = []
                style = ''
                # if SVM_TRAIN_WITHOUT_CATEGORY is True:
                #     style = 'front'
                style = 'front'
                path = os.path.dirname(os.path.dirname(save_embedding.get_image_path('http://test/noname', group_id, faceId, style)))
                # style = ''
                # if SVM_TRAIN_WITHOUT_CATEGORY is True:
                #     style = 'front'
                print("path={}".format(path)) #Frank
                path_exp = os.path.expanduser(path)
                classes = [path for path in os.listdir(path_exp) \
                                if os.path.isdir(os.path.join(path_exp, path))]
                classes.sort()
                nrof_classes = len(classes)
                #print("classes={}".format(classes)) #Frank
                for i in range(nrof_classes):
                    class_name = classes[i]
                    if USE_DEFAULT_DATA is True:
                        if class_name == "groupid_defaultfaceid":
                            continue;
                    facedir = os.path.join(path_exp, class_name)
                    image_paths = []
                    print("facedir={}".format(facedir))
                    if os.path.isdir(facedir):
                        images = os.listdir(facedir)
                        for img in images:
                            dataset.append(os.path.join(facedir,img))
                willRemoveCount = 0
                print("len(dataset)={}".format(len(dataset))) #Frank
                #print("dataset={}".format(dataset))
                #print("urlsInLocalDB={}".format(urlsInLocalDB))
                if len(dataset) > 0:
                    for image_path in dataset:
                        l5 = (item for item in urlsInLocalDB if item.filepath.replace('front/','') == image_path.replace('front/',''))
                        count = sum(1 for x in l5)
                        if count == 0:
                            print("sum={}".format(count))
                            willRemoveCount = willRemoveCount+1
                            print("image_path({}) only in local, remove it.".format(image_path))
                            if image_path and os.path.exists(image_path):
                                os.remove(image_path)
                                print("Remove image_path={}".format(image_path))
                            embedding_path = save_embedding.get_embedding_path(image_path)
                            if embedding_path and os.path.isfile(embedding_path):
                                os.remove(embedding_path)
                            if len(device_id) > 1 and len(toid) > 1:
                                message = 'image_path({}) only in local, remove it.'.format(image_path)
                                print(message)
                                sendMessage2Group(device_id, toid, message)
                if len(device_id) > 1 and len(toid) > 1:
                    message = 'Stat: localDB={}, server={}/{}, localfiles={}'.format(len(urlsInLocalDB), len(urlsOnServer), invalid_images_onserver, len(dataset)-willRemoveCount)
                    print(message)
                    sendMessage2Group(device_id, toid, message)
                return True
            else:
                print('response code != 200')
                return False
    except Exception as ex:
        print('disposeFinalSyncDatasetsThreadFunc: except:', ex)

def disposeSyncStatusInfoThreadFunc(device_id, toid):
    invalid_images_onserver = 0
    try:
        group_id = get_current_groupid()
        #host="http://localhost:3000/restapi/datasync/token/" + str(group_id)
        host = "http://workaihost.tiegushi.com/restapi/datasync/token/" + str(group_id)
        result = None
        try:
            response = urlopen(host, timeout=10)
        except HTTPError as e:
            print('HTTPError: ', e.code)
            return False
        except URLError as e:
            print('URLError: ', e.reason)
            return False
        except Exception as e:
            print('Error: ', e)
            return False
        else:
            # everything is fine
            if 200 == response.getcode():
                result = response.readline()
                #print(result)
                result = json.loads(result)

                #Remove invalid data from local DB
                urlsInLocalDB = TrainSet.query.filter_by(group_id=group_id).all()
                urlsOnServer = dict()
                for person in result:
                    faceId = person.get("faceId")
                    urls = person.get("urls")
                    for url in urls:
                        img_url = url['url']
                        faceid = faceId
                        style = url['style']
                        if style == 'left_side' or style == 'right_side' or style == 'lower_head' or style == 'blury':
                            invalid_images_onserver += 1
                            continue
                        urlsOnServer[img_url] = group_id, faceId, style
                print("Trainsets: len(urlsInLocalDB) = {}".format(len(urlsInLocalDB)))
                print("Trainsets: len(urlsOnServer) = {}".format(len(urlsOnServer)))

                #Remove invalid photos from local
                dataset = []
                # style = ''
                # if SVM_TRAIN_WITHOUT_CATEGORY is True:
                style = 'front'
                path = os.path.dirname(os.path.dirname(save_embedding.get_image_path('http://test/noname', group_id, faceId, style)))
                style = ''
                if SVM_TRAIN_WITHOUT_CATEGORY is True:
                    style = 'front'
                print("path={}".format(path)) #Frank
                path_exp = os.path.expanduser(path)
                classes = [path for path in os.listdir(path_exp) \
                                if os.path.isdir(os.path.join(path_exp, path))]
                classes.sort()
                nrof_classes = len(classes)
                #print("classes={}".format(classes)) #Frank
                for i in range(nrof_classes):
                    class_name = classes[i]
                    facedir = os.path.join(path_exp, class_name)
                    image_paths = []
                    print("facedir={}".format(facedir))
                    if os.path.isdir(facedir):
                        images = os.listdir(facedir)
                        for img in images:
                            dataset.append(os.path.join(facedir,img))
                if len(device_id) > 1 and len(toid) > 1:
                    message = 'StatInfo: localDB={}, server={}/{}, localfiles={}'.format(len(urlsInLocalDB), len(urlsOnServer), invalid_images_onserver, len(dataset))
                    print(message)
                    sendMessage2Group(device_id, toid, message)
                return True
            else:
                print('response code != 200')
                return False
    except Exception as ex:
        print('disposeSyncStatusInfoThreadFunc: except:', ex)

# @app.before_first_request
def migration():
    if os.path.exists('migrate_db.exe'):
        out_put = subprocess.check_output(['./migrate_db.exe', 'db', 'upgrade'])
    else:
        out_put = subprocess.check_output(['python', 'migrate_db.py', 'db', 'upgrade'])
    print(out_put)
    print('> finish migrate upgrade')


@app.route('/api/status', methods=['GET'])
def get_status():
    global isUpdatingDataSet
    if isUpdatingDataSet is False:
        resp = Response(json.dumps({"status":"alive"}), status=200, mimetype='application/json')
    else:
        resp = Response(json.dumps({"status":"busy"}), status=401, mimetype='application/json')
    return resp

@app.route('/api/images/<filename>', methods=['GET'])
def img(filename):
    # p = People.query.filter_by(filename=filename).first()
    # if p and p.aliyun_url:
    #     return redirect(p.aliyun_url)
    if os.path.isfile(os.path.join(app.config['UPLOAD_FOLDER'], filename)):
        # 返回图片
        return send_from_directory(app.config['UPLOAD_FOLDER'],
                                   filename)
        # 返回json
        # data = {'img_name': filename, 'img_url': request.url}
        # js = json.dumps(data)
        # resp = Response(js, status=200, mimetype='application/json')
        # return resp

    else:
        return abort(404)


def format_img_filename(old_filename):
    """
    给文件名加上gFlask_port，防止重名
    :param old_filename: 旧文件名
    :return: new_filename, uuid, ts
    """
    ext = old_filename.rsplit('.', 1)[-1]
    unix_time = time.time()
    uuid = request.args.get('uuid', '')
    ts = request.args.get('ts', str(unix_time * 1000))
    new_filename = uuid + '_' + str(gFlask_port) + '_' + str(unix_time).replace('.', '') + '_' + str(ts) + '.' + ext
    return new_filename, uuid, ts


@app.route('/api/upload_video/', methods=['POST'])
def upload_video():
    video_local_path = request.form.get('videopath')
    thumbnail_local_path = request.form.get('thumbnail', '')
    ts = int(time.time()*1000)  # 时间戳
    offset = time.timezone if (time.localtime().tm_isdst == 0) else time.altzone
    ts_offset = offset/60/60 * -1  # 时区 8
    uuid = request.args.get('uuid', '')
    key = uuid + str(ts)
    video_src = qiniu_upload_video(key+'video', video_local_path)  # 上传本地视频，获取视频播放地址
    video_post = qiniu_upload_img(key+'thumbnail', thumbnail_local_path)  # 视频封面预览图地址
    person_id = request.args.get('objid', '')

    if len(video_post) < 1:
        video_post = 'http://data.tiegushi.com/fTnmgpdDN4hF9re8F_1493176458747.jpg';

    payload = {'uuid': uuid,
              'person_id': person_id,
              'video_post': video_post,
              'video_src': video_src,
              'ts': ts,
              'ts_offset': ts_offset,
              }
    post2gst_video(payload)
    print('upload_video'.center(50,'-'))
    print(payload)
    return Response(json.dumps({"result": "ok"}), status=200, mimetype='application/json')

def sendDebugLogToGroup(uuid, current_groupid, message):
    if ENABLE_DEBUG_LOG_TO_GROUP is True:
        sendMessage2Group(uuid, current_groupid, message)

def showRecognizedImage(image_path, queue_index):
    if os.path.exists(image_path):
        recognized_img_path = os.path.join(os.path.dirname(image_path), 'face{}.png'.format(queue_index))
        shutil.copy(image_path, recognized_img_path)

FACE_COUNT = defaultdict(int)
OBJ_COUNT = 0
def updateDataSet(url, objId, group_id, device_id, drop, img_type, sqlId, style, img_ts, rm_reason):
    isUpdatingDataSet = True
    try:
        _updateDataSet(url, objId, group_id, device_id, drop, img_type, sqlId, style, img_ts, rm_reason)
    except Exception as ex:
        print("updateDataSet error:", ex)
        isUpdatingDataSet = False
        #raise
    isUpdatingDataSet = False

FAILEDDOWNLOADINFOFILE =  os.path.join(BASEDIR, 'failed_download_info.json')
FAILEDDOWNLOADINFOFILE2 =  os.path.join(BASEDIR, 'failed_download_info2.json')
fileMuxlock = threading.Lock()

def loadFailedDownloadInfo():
    failedDownloadInfo = {}
    failedDownloadInfo['dInfo'] = []
    if (os.path.isfile(FAILEDDOWNLOADINFOFILE)):
        with open(FAILEDDOWNLOADINFOFILE) as fJson:
            failedDownloadInfo = json.load(fJson)
    return failedDownloadInfo

def recordFailedDownload(url, group_id, face_id, style, device_id):
    failedDownloadInfo = loadFailedDownloadInfo()
    failedDownloadInfo['dInfo'].append({
        'url': url,
        'group_id': group_id,
        'face_id': face_id,
        'style': style,
        'device_id': device_id
    })
    with open(FAILEDDOWNLOADINFOFILE, 'w') as fJson:
        json.dump(failedDownloadInfo, fJson)


def loadFailedDownloadList(filepath):
    failedDownloadInfo = {}
    failedDownloadInfo['dInfo'] = []
    if (os.path.isfile(filepath)):
        with open(filepath) as fJson:
            failedDownloadInfo = json.load(fJson)
    return failedDownloadInfo

def addFailedDownloadInfo(url, group_id, face_id, style, device_id):
    fileMuxlock.acquire()
    failedDownloadInfo = loadFailedDownloadList(FAILEDDOWNLOADINFOFILE2)
    failedDownloadInfo['dInfo'].append({
        'url': url,
        'group_id': group_id,
        'face_id': face_id,
        'style': style,
        'device_id': device_id
    })
    print('addFailedDownloadInfo: url='+url)
    with open(FAILEDDOWNLOADINFOFILE2, 'w') as fJson:
        json.dump(failedDownloadInfo, fJson)
    fileMuxlock.release()

def mergeTwoJsonFiles():
    fileMuxlock.acquire()
    failedDownloadInfo1 = loadFailedDownloadList(FAILEDDOWNLOADINFOFILE)
    failedDownloadInfo2 = loadFailedDownloadList(FAILEDDOWNLOADINFOFILE2)
    mergedJson = {key: value for (key, value) in (failedDownloadInfo1.items() + failedDownloadInfo2.items())}
    if (len(mergedJson['dInfo']) > 0):
        print('mergeTwoJsonFiles: mergedJson=')
        for key, value in mergedJson.items():
            print(key, ':',  value)
        with open(FAILEDDOWNLOADINFOFILE, 'w') as fJson:
            json.dump(mergedJson, fJson)
    if (os.path.isfile(FAILEDDOWNLOADINFOFILE2)):
        os.remove(FAILEDDOWNLOADINFOFILE2)
    fileMuxlock.release()

def mergeFailedDownloadInfo(json1):
    fileMuxlock.acquire()
    failedDownloadInfo = loadFailedDownloadList(FAILEDDOWNLOADINFOFILE2)
    mergedJson = {key: value for (key, value) in (json1.items() + failedDownloadInfo.items())}
    if (len(mergedJson['dInfo']) > 0):
        print('mergeFailedDownloadInfo: mergedJson=')
        for key, value in mergedJson.items():
            print(key, ':',  value)
        with open(FAILEDDOWNLOADINFOFILE, 'w') as fJson:
            json.dump(mergedJson, fJson)
    if (os.path.isfile(FAILEDDOWNLOADINFOFILE2)):
        os.remove(FAILEDDOWNLOADINFOFILE2)
    fileMuxlock.release()

def downloadFunc():
    global FACE_COUNT
    global OBJ_COUNT

    while True:
        try:
            tmpFailedDownloadInfo = {}
            tmpFailedDownloadInfo['dInfo'] = []

            mergeTwoJsonFiles()
            failedDownloadInfo = loadFailedDownloadList(FAILEDDOWNLOADINFOFILE)
            for info in failedDownloadInfo['dInfo']:
                if SVM_TRAIN_WITHOUT_CATEGORY is True:
                    info['style'] = 'front'
                img_path = save_embedding.get_image_path(info['url'], info['group_id'], info['face_id'], info['style'])
                embedding_path = save_embedding.get_embedding_path(img_path)
                denoise_path = save_embedding.get_image_denoise_path(img_path)
                recreate_embedding = False
                if not os.path.exists(img_path):
                    img_path = save_embedding.download_img_for_svm(info['url'], info['group_id'], info['face_id'], style=info['style'])
                if img_path:
                    if not os.path.exists(denoise_path):
                        img = misc.imread(os.path.expanduser(img_path))
                        save_embedding.save_image_denoise(img, denoise_path)
                        recreate_embedding = True
                    if not os.path.exists(embedding_path) or recreate_embedding == True:
                        img = misc.imread(os.path.expanduser(denoise_path))  # 手动裁剪后的图片需要再缩放一下
                        aligned = misc.imresize(img, (image_size, image_size), interp='bilinear')
                        misc.imsave(img_path, aligned)
                        embedding = featureCalculation(img_path)
                        embedding_path = save_embedding.get_embedding_path(img_path)
                        save_embedding.create_embedding_string(embedding, embedding_path)
                    old_train_set = TrainSet.query.filter_by(url=info['url'], group_id=info['group_id'], is_or_isnot=True, style=info['style']).first()
                    if not old_train_set:
                        train = TrainSet(url=info['url'], group_id=info['group_id'], is_or_isnot=True,
                                         device_id=info['device_id'], face_id=info['face_id'], filepath=img_path, drop=False, style=info['style'])
                        db.session.add(train)
                        db.session.commit()
                        FACE_COUNT[info['style']] += 1
                        print('-> SVM {} style face count'.format((FACE_COUNT[info['style']])))
                else:
                    tmpFailedDownloadInfo['dInfo'].append({info})

            if (len(tmpFailedDownloadInfo['dInfo']) > 0):
                mergeFailedDownloadInfo(tmpFailedDownloadInfo)
                #with open(FAILEDDOWNLOADINFOFILE, 'w') as fJson:
                #    json.dump(failedDownloadInfo, fJson)
            elif (os.path.isfile(FAILEDDOWNLOADINFOFILE)):
                os.remove(FAILEDDOWNLOADINFOFILE)
        except Exception as ex:
            print('except:', ex)

        time.sleep(5)

tDownload = threading.Thread(target=downloadFunc)
tDownload.daemon = True
tDownload.start()

def dropPersonFunc(group_id, face_id, drop_person):
    print('dropPersonFunc, group_id:', group_id, 'face_id:', face_id, 'drop_person:', drop_person)

    try:
        if drop_person == 'true' or drop_person == 'True' or drop_person == True:
            with app.app_context():
                train_set = TrainSet.query.filter_by(group_id=group_id, face_id=face_id).all()
                dirname = None
                for t in train_set:
                    print('delete db, group_id:', group_id, 'face_id:', face_id, 'url:', t.url)
                    if t.filepath:
                        dirname = t.filepath
                    db.session.delete(t)
                    db.session.commit()

                if dirname:
                    dirname = dirname.rsplit('/', 1)[0]
                    print('dropPerson, remove dir:', dirname)
                    shutil.rmtree(dirname, ignore_errors=True)
    except Exception as ex:
        print('dropPersonFunc ex:', ex)

def generate_embedding_ifmissing(data_dir):
    if not os.path.exists(data_dir):
        print("generate_embedding_ifmissing: data_dir is not exists! Please check it.")
    dataset = facenet.get_dataset(data_dir)
    paths, labels = facenet.get_image_paths_and_labels(dataset)
    nrof_images = len(paths)
    for i in range(nrof_images):
        img_path = paths[i]
        embedding_path = save_embedding.get_embedding_path(img_path)
        denoise_path = save_embedding.get_image_denoise_path(img_path)
        print("denoise_path={}".format(denoise_path))
        recreate_embedding = False
        if not os.path.exists(denoise_path):
            img = misc.imread(os.path.expanduser(img_path))
            save_embedding.save_image_denoise(img, denoise_path)
            recreate_embedding = True
        if not os.path.exists(embedding_path) or recreate_embedding == True:
            embedding = featureCalculation2(denoise_path)
            save_embedding.create_embedding_string(embedding, embedding_path)
            print("Create missing embedding file: {}".format(embedding_path))


def check_default_data(group_id, style):
    """
    default_data is face data for SVM training. SVM training need at least two classes.
    Check if there is default data. If not, add default data.
    :param group_id:
    :param style:
    :return:
    """

    group_path = os.path.join(save_embedding.BASEPATH, group_id, style, save_embedding.img_dir)
    '''
    class_list = os.listdir(group_path)

    for one_class in class_list:
        class_id = one_class.split('_')[-1]
        # FIXME : Probably need to check all the files for default. Not just existence of image directory
        if class_id == 'default':
            return
    '''
    # Copy default face data
    default_dir_path = os.path.join(group_path, 'groupid_defaultfaceid')
    if not os.path.exists(default_dir_path):
        os.mkdir(default_dir_path)
    img_path = os.path.join(default_dir_path, 'default_face.png')
    if not os.path.isfile(img_path):
        default_data_path = os.path.join(BASEDIR, 'faces', 'default_data', 'default_face.png')
        shutil.copy(default_data_path, default_dir_path)
        # Generate denoise and embedding for default data
        img = misc.imread(os.path.expanduser(img_path))
        aligned = misc.imresize(img, (image_size, image_size), interp='bilinear')
        misc.imsave(img_path, aligned)
        '''
        denoise_path = save_embedding.get_image_denoise_path(img_path)
        save_embedding.save_image_denoise(aligned, denoise_path)
        '''
    embedding_path = save_embedding.get_embedding_path(img_path)
    if not os.path.isfile(embedding_path):
        embedding = featureCalculation2(img_path)
        save_embedding.create_embedding_string(embedding, embedding_path)


#updateDataSet(url=url, objId=face_id, group_id=group_id,drop=drop)
def _updateDataSet(url, objId, group_id, device_id, drop, img_type, sqlId, style, img_ts, rm_reason):
    print("> MQTT url:{}, objId:{}, drop:{}, gid:{}, sqlId:{}, style:{}, rm_reason:{}".format(url, objId, drop,
                                                                                group_id, sqlId, style, rm_reason))
    face_id = str(objId)

    if style is None:
        print('Need to update client app !')
        return
    styles = style.split('|')  # 如 ['left', 'rigth']

    global FACE_COUNT
    global OBJ_COUNT

    print("> MQTT2 url:{}, objId:{}, drop:{}, gid:{}, sqlId:{}, style:{}, rm_reason:{}, group_id:{}, drop:{}, img_type:{}".format(url, objId, drop,
                                                                                group_id, sqlId, style, rm_reason, group_id, drop, img_type))
    if (url is None) or (objId is None) or (group_id is None) or (drop is None) or (img_type is None):
        return
    if (len(url) < 1) or (len(objId) < 1) or (len(group_id) < 1) or (len(img_type) < 1):
        return

    if EN_OBJECT_DETECTION is False and img_type == 'object':
        return

    with app.app_context():
        #人脸: 未识别的图片点"删除"/合并的图片点"错"及点"删除", 在这里判断
        if img_type == 'face' and sqlId is not None and (drop == 'true' or drop == 'True' or drop == True):
            current_dirty_in_db = People.query.filter_by(aliyun_url=url, group_id=group_id).all()
            old_dirty_in_db = People.query.filter_by(id=sqlId, uuid=device_id).all()
            for d in old_dirty_in_db:
                #old_dirty_in_db 是最开始new people时候存的的对比数据
                print("remove origin dirty embedding url={}".format(d.aliyun_url))
                db.session.delete(d)
                db.session.commit()

            for t in current_dirty_in_db:
                if rm_reason is not None and rm_reason == "notface":
                    t.classId = "notface"
                    db.session.add(t)
                    db.session.commit()
                    print("update None-face image 1")
                    continue

                #删除当前图片
                print("remove current dirty embedding sqlId={}".format(sqlId))
                db.session.delete(t)
                db.session.commit()

        #if SVM_CLASSIFIER_ENABLED is False:
        for style in styles:
            if style == 'dirty' or style == 'low_pixel' or style == 'blury':
                continue
        train_set = TrainSet.query.filter_by(url=url, group_id=group_id, style=style).all()
        people_in_db = People.query.filter_by(group_id=group_id, aliyun_url=url).all()
        if drop == 'true' or drop == 'True' or drop is True:
            print(rm_reason)
            if len(people_in_db) == 0 and rm_reason is not None and rm_reason == "notface":
                print("insert not face image into people db")
                url_tmp=url.split('/')
                if len(url_tmp) > 0:
                    imgfilepath = save_embedding.download_img_only(url, 'tempdir')
                    insertOneImageIntoPeopleDB(imgfilepath, device_id, group_id, objId, url, notFace=True, style=style)

            for t in train_set:
                t.drop = True
                db.session.delete(t)
                db.session.commit()
                #db.session.delete(t)

                #delete the train image
                filepath = t.filepath
                print('drop train_set db:', filepath)
                if filepath and os.path.exists(filepath):
                    os.remove(filepath)
            for t in people_in_db:
                if rm_reason is not None and rm_reason == "notface":
                    t.classId = "notface"
                    db.session.add(t)
                    db.session.commit()
                    print("update None-face image 2")
                    continue

                print('drop people_in_db db & filepath:')
                db.session.delete(t)
                db.session.commit()

            # labeled_img[person_id].remove(url)
        else:
            embedding = None
            if len(people_in_db) == 0:
                print("insert into people db")
                url_tmp=url.split('/')
                if len(url_tmp) > 0:
                    imgfilepath = save_embedding.download_img_only(url, 'tempdir')
                    embedding = insertOneImageIntoPeopleDB(imgfilepath, device_id, group_id, objId, url, notFace=False, style=style)
            else:
                for t in people_in_db:
                    print('update people_in_db classId %s as %s' %(t.classId, objId))
                    t.classId = objId
                    db.session.add(t)
                    db.session.commit()

            old_train_set = TrainSet.query.filter_by(url=url, group_id=group_id, is_or_isnot=True, style=style).first()
            print("old_train_set: {}, {}".format(old_train_set, url))
            if not old_train_set:
                print("insert one in db")
                if SVM_TRAIN_WITHOUT_CATEGORY is True:
                    style = 'front'
                train = TrainSet(url=url, group_id=group_id, is_or_isnot=True,
                                 device_id=device_id, face_id=face_id, filepath='', drop=False, style=style)
                db.session.add(train)
                db.session.commit()
                if img_type == 'object' and EN_OBJECT_DETECTION is True:
                    infile = gbottlenecks.downloadImg(url, group_id, face_id, train.id)
                    print(infile)  # 原图路径
                    resize(infile)
                    os.remove(infile)  # 保存resized的图片，删除原图
                    gbottlenecks.createAndCacheBottlenecks()
                    OBJ_COUNT += 1
                    train.filepath = infile
                elif SVM_CLASSIFIER_ENABLED is True:
                    img_path = save_embedding.download_img_for_svm(url, group_id, face_id, style=style)
                    if img_path:
                        img = misc.imread(os.path.expanduser(img_path))  # 手动裁剪后的图片需要再缩放一下
                        aligned = misc.imresize(img, (image_size, image_size), interp='bilinear')
                        misc.imsave(img_path, aligned)

                        denoise_path = save_embedding.get_image_denoise_path(img_path)
                        save_embedding.save_image_denoise(aligned, denoise_path)

                        embedding = featureCalculation2(denoise_path)
                        embedding_path = save_embedding.get_embedding_path(img_path)
                        save_embedding.create_embedding_string(embedding, embedding_path)
                        FACE_COUNT[style] += 1
                        train.filepath = img_path
                        print('-> insert: SVM {} style face count, url={}'.format((FACE_COUNT[style]), url))
                    else:
                        print('download failed, save to json file for future download: url={}'.format(url))
                        #recordFailedDownload(url, group_id, face_id, style, device_id)
                        addFailedDownloadInfo(url, group_id, face_id, style, device_id)
                else:
                    print('face')
                    # 人脸训练过程：标注人脸 > 下载人脸对应URL图片 > 保存对应embedding并转换 > 训练

                    img_path = save_embedding.download_img(url, group_id, face_id, img_id=train.id, style=style)
                    img = misc.imread(os.path.expanduser(img_path))  # 手动裁剪后的图片需要再缩放一下
                    aligned = misc.imresize(img, (image_size, image_size), interp='bilinear')
                    misc.imsave(img_path, aligned)
                    embedding = featureCalculation2(img_path)
                    embedding_path = save_embedding.get_embedding_path(img_path)
                    save_embedding.create_embedding_string(embedding, embedding_path)
                    FACE_COUNT[style] += 1
                    train.filepath = img_path
                    print('{} style face count'.format((FACE_COUNT[style])))

                db.session.add(train)
                db.session.commit()

            elif old_train_set and old_train_set.face_id != face_id:
                print("update one in db, url={}".format(url))
                if old_train_set.drop == True:
                    print("this url is droped")
                    return
                # url中的face不是 xxx
                if SVM_TRAIN_WITHOUT_CATEGORY is True:
                    style = 'front'
                old_train_set.is_or_isnot = False
                db.session.add(old_train_set)
                db.session.commit()
                # url中的face是 xxx
                new_train_set = TrainSet(url=url, group_id=group_id, is_or_isnot=True, device_id=device_id,
                                         face_id=face_id, style=style)
                db.session.add(new_train_set)
                db.session.commit()
                if img_type == 'object' and EN_OBJECT_DETECTION is True:
                    infile = gbottlenecks.downloadImg(url, group_id, face_id, new_train_set.id)
                    resize(infile)
                    os.remove(infile)  # 保存resized的图片，删除原图
                    gbottlenecks.createAndCacheBottlenecks()
                    OBJ_COUNT += 1

                    # 这里需要把老图从本地目录删除掉
                    old_img_path = infile.replace(str(new_train_set.id)+'.jpg', str(old_train_set.id)+'.jpg')
                    os.remove(old_img_path)
                elif SVM_CLASSIFIER_ENABLED is True:
                    img_path = save_embedding.download_img_for_svm(url, group_id, face_id, style=style)
                    if img_path:
                        denoise_path = save_embedding.get_image_denoise_path(img_path)
                        recreate_embedding = False
                        if not os.path.exists(denoise_path):
                            img = misc.imread(os.path.expanduser(img_path))
                            save_embedding.save_image_denoise(img, denoise_path)
                            recreate_embedding = True

                        embedding_path = save_embedding.get_embedding_path(img_path)
                        if os.path.isfile(embedding_path) is False:
                            #img = misc.imread(os.path.expanduser(img_path))  # 手动裁剪后的图片需要再缩放一下
                            #aligned = misc.imresize(img, (image_size, image_size))
                            #misc.imsave(img_path, aligned)
                            if embedding is None:
                                embedding = featureCalculation(denoise_path)
                            save_embedding.create_embedding_string(embedding, embedding_path)
                        FACE_COUNT[style] += 1
                        print('update: {} style face count, url={}'.format(FACE_COUNT[style], url))

                        # 这里需要把老图从本地目录删除掉
                        old_img_path = img_path.replace(str(new_train_set.id) + '.jpg', str(old_train_set.id) + '.jpg')
                        os.remove(old_img_path)
                else:
                    print('face')
                    img_path = save_embedding.download_img(url, group_id, face_id, img_id=new_train_set.id, style=style)
                    #img = misc.imread(os.path.expanduser(img_path))  # 手动裁剪后的图片需要再缩放一下
                    #aligned = misc.imresize(img, (image_size, image_size))
                    #misc.imsave(img_path, aligned)
                    embedding = featureCalculation(img_path)
                    embedding_path = save_embedding.get_embedding_path(img_path)
                    save_embedding.create_embedding_string(embedding, embedding_path)
                    FACE_COUNT[style] += 1
                    print('{} style face count'.format((FACE_COUNT[style])))

                    # 这里需要把老图从本地目录删除掉
                    old_img_path = img_path.replace(str(new_train_set.id) + '.jpg', str(old_train_set.id) + '.jpg')
                    os.remove(old_img_path)

            else:
                print("already in dataset")

        if USE_DEFAULT_DATA is True:
            check_default_data(group_id, style)

        if img_type == 'object':
            # all_dataset = TrainSet.query.filter_by(group_id=group_id, face_id=face_id, is_or_isnot=True).all()
            # cnt = TrainSet.query.filter_by(group_id=group_id, face_id=face_id, is_or_isnot=True).count()
            if OBJ_COUNT > 0 and OBJ_COUNT % 20 == 0:
                #sendMessage2Group(device_id, group_id, "Training now ...")
                clean_droped_embedding(group_id)
                print("training now ...")
                if os.path.exists('objects/train_obj.exe'):
                    os.system("./objects/train_obj.exe {} {}".format(deviceId, group_id))
                elif os.path.exists('objects/train_obj.pyc'):
                    os.system("python objects/train_obj.pyc {} {}".format(deviceId, group_id))
                else:
                    os.system("python objects/train_obj.py {} {}".format(deviceId, group_id))
        else:
            current_groupid = get_current_groupid()
            if SVM_CLASSIFIER_ENABLED is True and FACE_COUNT[style] > 0 and FACE_COUNT[style] % 10 == 0:
                # #http://sharats.me/the-ever-useful-and-neat-subprocess-module.html
                # #https://stackoverflow.com/questions/2837214/python-popen-command-wait-until-the-command-is-finished
                if mqttc is not None:
                    mqttc.train_svm(device_id, current_groupid, "Auto training triggered ...")
                '''
                clean_droped_embedding(current_groupid)

                svm_current_groupid_basepath = os.path.join('data', 'faces', current_groupid)

                if len(device_id) > 1 and len(current_groupid) > 1:
                    sendMessage2Group(device_id, current_groupid, "Auto training triggered ...")
                stime = time.time()
                # for style in ['left_side', 'right_side', 'front']:
                for style in ['front']:
                    #style = 'front'
                    svm_train_dataset = os.path.join(svm_current_groupid_basepath, style, 'face_embedding')
                    if not os.path.exists(svm_train_dataset):
                        continue
                    svn_train_pkl = os.path.join(svm_current_groupid_basepath, style, 'classifier_182.pkl')
                    args_list = ['TRAIN', svm_train_dataset, 'facenet_models/20170512-110547/20170512-110547.pb',
                                 svn_train_pkl, '--batch_size', '1000']
                    generate_embedding_ifmissing(svm_train_dataset)
                    ret_val = classifer.train_svm_with_embedding(args_list)
                    message = "Failed"
                    if ret_val is None:
                        message = "Failed"
                    else:
                        if ret_val is "OK":
                            train_cost = round(time.time() - stime,2)
                            message = '-> Train cost {}s'.format(train_cost)
                        else:
                            message = ret_val
                    print('-> Train {} SVM cost {}s'.format(style, time.time() - stime))

                    if len(device_id) > 1 and len(current_groupid) > 1:
                        sendMessage2Group(device_id, current_groupid, message)
                '''
            elif EN_SOFTMAX is True and FACE_COUNT[style] > 0 and FACE_COUNT[style] % 20 == 0:
                clean_droped_embedding(group_id)
                print("training on embedding now ...")
                if os.path.exists('faces/train_faces.exe'):
                    output = subprocess.check_output(['./faces/train_faces.exe', current_groupid, style])
                    # s = subprocess.Popen('python ./faces/train_faces.exe {} {}'.format(current_groupid, style), shell=True)
                elif os.path.exists('faces/train_faces.pyc'):
                    output = subprocess.check_output(['python', 'faces/train_faces.pyc', current_groupid, style])
                    # s = subprocess.Popen('python ./faces/train_faces.pyc {} {}'.format(current_groupid, style), shell=True)
                else:
                    output = subprocess.check_output(['python', 'faces/train_faces.py', current_groupid, style])
                    # s = subprocess.Popen('python ./faces/train_faces.py {} {}'.format(current_groupid, style), shell=True)
                print(output)
                # os.system("python faces/train_faces.py")  # 两种外挂训练方式


## 用户手动label时，更新自动标注训练集
# labeled_img = {}
def updata_trainset(json):
    print("legacy trainset ignored")
    return
    # 接收json格式数据
    data = json
    url       = data.get('url')
    person_id = data.get('person_id')
    device_id = data.get('device_id')
    face_id   = data.get('face_id')
    drop      = data.get('drop')

    if (url is None) or (person_id is None) or (device_id is None) or (face_id is None) or (drop is None):
        return

    with app.app_context():
        if drop == 'true' or drop == 'True' or drop == True:
            train_set = TrainSet.query.filter_by(url=url, device_id=device_id).all()
            for t in train_set:
                db.session.delete(t)
            db.session.commit()
            # labeled_img[person_id].remove(url)
        else:
            old_train_set = TrainSet.query.filter_by(url=url, device_id=device_id, is_or_isnot=True).first()  # 一张图片对应的人是唯一的
            if old_train_set and old_train_set.face_id != int(face_id):
                # url中的face不是 xxx
                old_train_set.is_or_isnot = False
                db.session.add(old_train_set)
                db.session.commit()
                # url中的face是 xxx
                new_train_set = TrainSet(url=url,
                                         embed=old_train_set.embed,
                                         is_or_isnot=True,
                                         person_id=person_id,
                                         device_id=device_id,
                                         face_id=face_id,
                                         )
                db.session.add(new_train_set)
                db.session.commit()
                print(old_train_set)
                print(new_train_set)

            # 存储一个单独的字典文件保存手动label过的url
            # if not labeled_img.has_key(person_id):
            #     labeled_img[person_id] = set([])
            # labeled_img[person_id].add(url)

@app.route('/api/tablet/', methods=['POST'])
def sync_config():
    cmd_type = request.args.get('type', '')
    print(cmd_type)
    if cmd_type is not None and len(cmd_type) > 1:
        if cmd_type == 'group':
            uuid = request.args.get('uuid', '')
            group_id = request.args.get('group_id', '')
            print(uuid)
            print(group_id)
            if uuid is not None and len(uuid) > 1:
                print("uuid=%s got group event, going to reconnect mqtt" %(uuid))
                #清空一下group_id,不然不会从服务器重新获取group_id
                save_groupid_to_file('')
                mqttc.reSubscribeGroup(uuid)
    time.sleep(2)
    return Response(json.dumps({"result":"ok"}), status=200, mimetype='application/json')

@app.errorhandler(404)
def not_found(error=None):
    message = {
        'status': 404,
        'message': 'Not Found ' + request.url,
    }
    return make_response(json.dumps(message), 404)


# 测试上传
@app.route('/test/upload')
def upload_test():
    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form method=post action=/api/images enctype=multipart/form-data>
      <p><input type=file name=file>
         <input type=submit value=Upload>
    </form>
    '''
def parse_arguments(argv):
    parser = argparse.ArgumentParser()

    parser.add_argument('--report', dest='report', action='store_true')
    parser.add_argument('--no-report', dest='report', action='store_false')
    parser.set_defaults(report=True)

    parser.add_argument('--port', type=int,
        help='The port server listen on', default=5000)
    parser.add_argument('--host', type=str,
        help='The ip server listen on', default='0.0.0.0')
    return parser.parse_args(argv)

def mqttDebugOnOff(MQTTDebugFlag):
    global ENABLE_DEBUG_LOG_TO_GROUP
    if MQTTDebugFlag is False or MQTTDebugFlag is True:
        ENABLE_DEBUG_LOG_TO_GROUP = MQTTDebugFlag


def crons_start():
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    if not os.path.exists(os.path.join(BASEDIR, 'data', 'data.sqlite')):
        db.create_all()

svm_face_dataset=None
svm_face_embedding=None
svm_tmp_dir=None
svm_face_testdataset=None
svm_stranger_testdataset=None

def init_fs():
    global svm_face_dataset
    global svm_face_embedding
    global svm_tmp_dir
    global svm_face_testdataset
    global svm_stranger_testdataset

    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    # if not os.path.exists(os.path.join(BASEDIR, 'data.sqlite')):
    #     db.create_all()
    if not os.path.exists(os.path.join(BASEDIR, 'data', 'data.sqlite')):
        if os.path.exists(os.path.join(BASEDIR, 'data_init')):
            shutil.copyfile(os.path.join(BASEDIR, 'data_init'), os.path.join(BASEDIR, 'data', 'data.sqlite'))

    if not os.path.exists(TMP_DIR_PATH):
        os.makedirs(TMP_DIR_PATH)

    if SVM_CLASSIFIER_ENABLED:
        svm_face_dataset = os.path.join(BASEDIR, 'data', 'face_dataset')
        svm_face_embedding = os.path.join(BASEDIR, 'data', 'face_embedding')
        svm_tmp_dir = os.path.join(BASEDIR, 'data', 'faces', 'noname', 'person')
        svm_face_testdataset = os.path.join(BASEDIR, 'data', 'face_testdataset')
        svm_stranger_testdataset = os.path.join(BASEDIR, 'data', 'stranger_testdataset')
        if not os.path.exists(svm_face_dataset):
            os.mkdir(svm_face_dataset)
        if not os.path.exists(svm_face_embedding):
            os.mkdir(svm_face_embedding)
        if not os.path.exists(svm_tmp_dir):
            os.makedirs(svm_tmp_dir)
        if not os.path.exists(svm_face_testdataset):
            os.mkdir(svm_face_testdataset)
        if not os.path.exists(svm_stranger_testdataset):
            os.mkdir(svm_stranger_testdataset)

def init_mqtt_client():
    #TODO: UUID when no eth0/wlan0
    device_id = get_deviceid()
    mqttc = MyMQTTClass(device_id + str(5000))
    mqttc.initialize(updata_trainset, disposeAutoGroupFunc)
    mqttc.registerUpateTrainsetHandle(updateDataSet)
    mqttc.registerMQTTDebugOnOffHandle(mqttDebugOnOff)
    mqttc.registerDropPersonHandle(dropPersonFunc)
    mqttc.registerMQTTFinalSyncDatasetsHandle(disposeFinalSyncDatasetsThreadFunc)
    mqttc.registerMQTTSyncStatusInfoHandle(disposeSyncStatusInfoThreadFunc)
    mqttc.registerMQTTGenerateEmbeddingIfMissingHandle(generate_embedding_ifmissing)
    mqttc.start()

def update_frame_db(camera_id=None, device_id=None, group_id=None, blury=None, img_path=None, img_style=None, accuracy=None, url=None, num_face=None, tracking_id=None, time_stamp=None, tracking_flag=None):
    #uuid = db.Column(db.String(64))
    #group_id = db.Column(db.String(64))
    #blury = db.Column(db.Integer)
    #img_path = db.Column(db.String(128))
    #img_style = db.Column(db.String(64))
    #accuracy = db.Column(db.Float)
    #url = db.Column(db.String(128))
    #num_face = db.Column(db.Integer)
    #tracking_id = db.Column(db.String(64))
    #device_id = db.Column(db.String(64))
    #time_stamp = db.Column(db.Integer)
    #tracking_flag = db.Column(db.String(64))

    if img_path is None or group_id is None:
        return

    with app.app_context():
        frame = Frame.query.filter_by(group_id=group_id, img_path=img_path).first()
        if frame is None:
            new_frame = Frame(camera_id=camera_id, group_id=group_id, blury=blury, img_path=img_path,
                              img_style=img_style, accuracy=accuracy, url=url, num_face=num_face,
                              tracking_id=tracking_id, device_id=device_id, time_stamp=time_stamp, tracking_flag=tracking_flag)
            db.session.add(new_frame)
            print("insert in db: {}".format(new_frame))
        else:
            if blury is not None:
                frame.blury = blury
            if img_style is not None:
                frame.img_style = img_style
            if accuracy is not None:
                frame.accuracy = accuracy
            if url is not None:
                frame.url = url
            if num_face is not None:
                frame.num_face = num_face
            if tracking_id is not None:
                frame.tracking_id = tracking_id
            if time_stamp is not None:
                frame.time_stamp = time_stamp
            if tracking_flag is not None:
                frame.tracking_flag = tracking_flag

            db.session.add(frame)
            print("update db: {}".format(frame))
        db.session.commit()

def getQueueName():
    if os.environ is not None and 'WORKER_TYPE' in os.environ.keys():
        return os.environ['WORKER_TYPE']
    return ""

def featureCalculation2(imgpath):
    embedding=None
    if HAS_OPENCL == 'false':
        with open(imgpath, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read())
        embedding = get_remote_embedding(encoded_string)
    else:
        embedding = FaceProcessing.FaceProcessingImageData2(imgpath)
    return embedding

@worker_process_init.connect()
def setup(sender=None, **kwargs):
    global mqttc

    # setup
    print('done initializing <<< ==== be called Per Fork/Process')
    _type=getQueueName()
    if _type == "embedding":

        check_groupid_changed()
        init_fs()

        if HAS_OPENCL == 'true':
            mod = FaceProcessing.init_embedding_processor()
            print("start to warm up")
            embedding = featureCalculation2(os.path.join(BASEDIR,"image","Mike_Alden_0001_tmp.png"))
            print("warmed up")
        #if embedding is not None:
        #    print("worker embedding ready")

        init_mqtt_client()

    return "detect"


class FaceDetectorTask(Task):
    def __init__(self):
        self._model = 'testing'
        self._type = getQueueName()
        print(">>> {}".format(self._type))

@deepeye.task
def extract_v2(image):
    # print(">>> extract() {} ".format(image))
    imgstring=image["base64data"]
    imgpath=image["path"]
    style=image["style"]
    blury=image["blury"]
    ts=image["ts"]
    trackerid=image["trackerid"]
    totalPeople=image["totalPeople"]
    uuid = get_deviceid()
    current_groupid = get_current_groupid()

    if current_groupid is None:
        return json.dumps({"embedding_path":"","error":"please join group"})
    if HAS_OPENCL == 'false':
        embedding = get_remote_embedding(imgstring)
    else:
        embedding = FaceProcessing.FaceProcessingBase64ImageData2(imgstring)
    embedding_path=''
    embedding_str=''
    if embedding is not None:
        if type(trackerid) is not str:
            trackerid = str(trackerid)
        embedding_str = save_embedding.convert_embedding_to_string(embedding)
        return json.dumps({"embedding_str":embedding_str})
    else:
        return json.dumps({"error":"please check your configuration"})

deepeye.conf.task_routes = {
    'upload_api-v2.extract_v2': {'queue': 'embedding'}
}

if __name__ == '__main__':
    deepeye.start()
