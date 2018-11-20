# coding=utf-8
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os, json, time, sys, thread
import argparse
import unicodedata
import cv2
import shutil
import subprocess
import threading
# import dlib
import math
import time
import os.path
import Queue
from threading import Timer

from collections import defaultdict
from flask import Flask, request, url_for, make_response, abort, Response, jsonify, send_from_directory, redirect
from flask_sqlalchemy import SQLAlchemy
from migrate_db import People, TrainSet, db, AutoGroupSet, Stranger
from sqlalchemy import exc
#from flask_script import Server, Manager
#from flask_migrate import Migrate, MigrateCommand
#from werkzeug.utils import secure_filename
from uuid import uuid1
import urllib2
from urllib2 import Request, urlopen, URLError, HTTPError

from PIL import Image
import tensorflow as tf
import numpy as np
from scipy import misc
from math import hypot
from multiprocessing import Process
from collections import OrderedDict

SAVE_FULL_BODY=True

import facenet
import align.detect_face
if SAVE_FULL_BODY is True:
    from align.align_dataset_mtcnn_crop_body import save_body_by_face_position_jpg
# from align import align_dlib
import classifier_classify_new
import clustering_people
from subprocess import Popen, PIPE

import FaceProcessing
from utilslib.uploadFile import uploadFileInit
from utilslib.mqttClient import MyMQTTClass
from utilslib.persistentUUID import getUUID
from utilslib.save2gst import save2gst, post2gst_motion, post2gst_video
from utilslib.save2gst import sendMessage2Group
from utilslib.getDeviceInfo import deviceId, get_current_groupid, get_deviceid, save_groupid_to_file
from utilslib.qiniuUpload import qiniu_upload_img, qiniu_upload_video, qiniu_upload_data, SUFFIX
# from utilslib.make_a_gif import load_all_images, build_gif, url_to_image
# from utilslib.timer import Timer
from utilslib.clean_droped_data import clean_droped_embedding

from objects.generate_bottlenecks import GenerateBottlenecks, resize
from objects.train_obj import TrainFromBottlenecks, train_from_bottlenecks
from objects.test_on_bottleneck import test_on_bottleneck
from Mobilenet.generate_bottlenecks import MobilenetBottlenecks, download_img_for_body, get_embedding_path_for_body, down_embedding_for_body
from Mobilenet.test_on_bottleneck import predict
from faces import save_embedding, test_on_embedding

from utilslib.resultqueue import push_resultQueue, get_resultQueue

BASEDIR = os.getenv('RUNTIME_BASEDIR',os.path.abspath(os.path.dirname(__file__)))
TMP_DIR_PATH = os.path.join(BASEDIR, 'faces', 'tmp_pic_path')
UPLOAD_FOLDER = os.path.join(BASEDIR, 'image')
DATABASE = 'sqlite:///' + os.path.join(BASEDIR, 'data.sqlite')
face_tmp_objid = None
obje_tmp_objid = None
EN_OBJECT_DETECTION = False
FACE_DETECTION_WITH_DLIB = False # Disable DLIB at this time
EN_SOFTMAX = False
SOFTMAX_ONLY = False

isUpdatingDataSet = False

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
DO_NOT_UPLOAD_IMAGE = True
DO_NOT_REPORT_TO_SERVER = True
NEAR_FRONTIAL_ONLY = False

image_size = 160
margin = 16
facenet_model = os.path.join(BASEDIR, 'facenet_models/20170512-110547/20170512-110547.pb')
minsize = 50  # minimum size of face
threshold = [0.6, 0.7, 0.7]  # three steps's threshold
factor = 0.709  # scale factor
confident_value = 0.67
mineyedist = 0.3 # Eye distance of width of face bounding box
CONFIDENT_VALUE_THRESHOLD = 0.80 #点圈显示的匹配度阈值，大于这个才显示,针对数据库遍历

BLURY_THREHOLD = 20 # Blur image if less than it. Reference: http://www.pyimagesearch.com/2015/09/07/blur-detection-with-opencv/

uploadImg=None
mqttc=None
gbottlenecks=None
trainfromfottlenecks=None
gFlask_port=None
preFrameOnDevice = {}
all_face_index = 0 #每当识别出一个人脸就+1，当2个人同时出现在图片里面并且都不认识，需要区分开来

SAVE_ORIGINAL_FACE = False
original_face_img_path = os.path.join(BASEDIR, 'original_face_img')
if not os.path.exists(original_face_img_path):
    os.mkdir(original_face_img_path)

SVM_CLASSIFIER_ENABLED=True
SVM_SAVE_TEST_DATASET=True
SVM_TRAIN_WITHOUT_CATEGORY=True
SVM_HIGH_SCORE_WITH_DB_CHECK=True

sess, graph = FaceProcessing.InitialFaceProcessor(facenet_model)

if FACE_DETECTION_WITH_DLIB is False:
    graph2 = tf.Graph()
    with graph2.as_default():
        sess2 = tf.Session(config=tf.ConfigProto(log_device_placement=False), graph=graph2)
        with sess2.as_default():
            pnet, rnet, onet = align.detect_face.create_mtcnn(sess2, None)
else:
    dlibFacePredictor = os.path.join(BASEDIR,'../models',
                                 "shape_predictor_68_face_landmarks.dat")  # 特征提取器
    dlibAlign = align_dlib.AlignDlib(dlibFacePredictor)  # 装载特征提取器，实例化AlignDlib类; 默认用了dlib自带的人脸检测器


def dlibImageProcessor(imgPath):
    """
    dlib 处理图片
    :param imgPath:
    :return: 包含图片路径与 prewhitened 的 dict
    """
    bgrImg = cv2.imread(imgPath)
    if bgrImg is None:
        raise Exception("Unable to load image: {}".format(imgPath))
    rgbImg = cv2.cvtColor(bgrImg, cv2.COLOR_BGR2RGB)
    # assert np.isclose(norm(rgbImg), 11.1355)

    dets = dlibAlign.getAllFaceBoundingBoxes(rgbImg)

    # dets的元素个数即为脸的个数
    print("Number of faces detected: {}".format(len(dets)))

    face_path = {}  # 存放多个脸部图片及prewhitened
    blury_arr = {}

    # 使用enumerate 函数遍历序列中的元素以及它们的下标
    # 下标i即为人脸序号
    for i, bb in enumerate(dets):
        if bb is not None:
            alignedFace = dlibAlign.align(160, rgbImg, bb)  # 缩放裁剪对齐
            gray_face = cv2.cvtColor(alignedFace, cv2.COLOR_BGR2GRAY)
            blury_value = cv2.Laplacian(gray_face, cv2.CV_64F).var()
            if blury_value < BLURY_THREHOLD:
                print('A blur face (%d) captured, avoid it.' % blury_value)
                #continue
            else:
                print('Blur Value: %d, good' % blury_value)
            prewhitened = facenet.prewhiten(alignedFace)
            tmp_image_path = imgPath.rsplit('.', 1)[0] + str(i) + '.' + imgPath.rsplit('.', 1)[1]
            misc.imsave(tmp_image_path, alignedFace)  # 保存为图像
            face_path[tmp_image_path] = prewhitened
            blury_arr[tmp_image_path] = blury_value
    return face_path, blury_arr


def is_acute(c_1, c_2, c_3):
    dist_12 = math.hypot(c_1[0] - c_2[0], c_1[1] - c_2[1])
    dist_23 = math.hypot(c_2[0] - c_3[0], c_2[1] - c_3[1])
    dist_13 = math.hypot(c_1[0] - c_3[0], c_1[1] - c_3[1])

    my_list = [dist_12, dist_23, dist_13]
    my_list.sort()
    if math.pow(my_list[0], 2) + math.pow(my_list[1], 2) - math.pow(my_list[2], 2) > 0:
        return True
    else:
        return False

counter = 0

def load_align_image(image_path, sess, graph, pnet, rnet, onet):
    img = misc.imread(os.path.expanduser(image_path))
    img_size = np.asarray(img.shape)[0:2]
    with graph2.as_default():
        with sess2.as_default():
            bounding_boxes, bounding_points = align.detect_face.detect_face(img, minsize, pnet, rnet, onet, threshold, factor)
    nrof_faces = bounding_boxes.shape[0]  # 人脸数目
    width = img_size[1]
    height = img_size[0]
    if nrof_faces > 0:
        face_path = {}  # 存放多个脸部图片
        blury_arr = {}
        imgs_style = {}  # 存放不同人脸图对应的类型，如左侧、右侧、低头、抬头、低像素、过模糊、标准
        face_body = {}  # 人脸对应的人体图片路径
        #print('The number of faces detected: {}'.format(nrof_faces))
        for i in range(nrof_faces):  # 遍历所有faces
            style = []
            det = np.squeeze(bounding_boxes.copy()[i, 0:4])
            # det = np.squeeze(align.detect_face.rerec(bounding_boxes.copy())[i, 0:4])
            bounding_point = bounding_points[:, i]  # 按i获取多个人脸的point
            bb = np.zeros(4, dtype=np.int32)  # 坐标
            bb[0] = np.maximum(det[0] - margin / 2, 0)
            bb[1] = np.maximum(det[1] - margin / 2, 0)
            bb[2] = np.minimum(det[2] + margin / 2, img_size[1])
            bb[3] = np.minimum(det[3] + margin / 2, img_size[0])

            if bb[0] == 0 or bb[1] == 0 or bb[2] >= width or bb[3] >= height:
                print('Out of boundary ({},{},{},{})'.format(bb[0],bb[1],bb[2],bb[3]))
                continue
            else:
                eye_1 = [bounding_point[0], bounding_point[5]]
                eye_2 = [bounding_point[1], bounding_point[6]]
                nose = [bounding_point[2], bounding_point[7]]
                mouth_1 = [bounding_point[3], bounding_point[8]]
                mouth_2 = [bounding_point[4], bounding_point[9]]
                face_width = bb[2] - bb[0]
                face_height = bb[3] - bb[1]
                if face_width * face_height  < minsize * minsize:
                    print("to small to recognise ({},{})".format(face_width,face_height))
                    continue
                else:
                    middle_point = (bb[2] + bb[0])/2
                    y_middle_point = (bb[3] + bb[1]) / 2
                    print('eye_1[0]={}, eye_2[0]={}, middle_point={}, bounding_point[5]={}, bounding_point[6]={}, y_middle_point={}'.format(eye_1[0], eye_2[0], middle_point, bounding_point[5], bounding_point[6], y_middle_point))
                    if eye_1[0] > middle_point:
                        print('(Left Eye on the Right) Add style')
                        style.append('left_side')
                        # continue
                    elif eye_2[0] < middle_point:
                        print('(Right Eye on the left) Add style')
                        style.append('right_side')
                        # continue
                    elif max(bounding_point[5], bounding_point[6]) > y_middle_point:
                        print('(Eye lower than middle of face) Skip')
                        style.append('lower_head')
                        # continue
                        # 左右两个眼睛最低的y轴，低于图片的中间高度，就认为是低头
                    #    style.append('lower_head')
                    #elif bounding_point[7] < y_middle_point:
                        # 鼻子的y轴高于图片的中间高度，就认为是抬头
                    #    style.append('raise_head')
                    else:
                        style.append('front')
                        #print('Good Face')

                if SAVE_FULL_BODY is True:
                    file_path_to_save = image_path.rsplit('.', 1)[0] + '_' + str(i) + '_t1.' + 'jpg'
                    result, width_ratio, height_ratio = save_body_by_face_position_jpg(bb,img,file_path_to_save)

                cropped = img[bb[1]:bb[3], bb[0]:bb[2], :]  # 裁剪
                aligned = misc.imresize(cropped, (160, 160), interp='cubic')  # 缩放图像

                # Need to detect if face is too blury to be detected
                gray_face = cv2.cvtColor(aligned, cv2.COLOR_BGR2GRAY)
                blury_value = cv2.Laplacian(gray_face, cv2.CV_64F).var()
                if blury_value < BLURY_THREHOLD:
                    print('A blur face (%d) captured, avoid it.' %blury_value)
                    style = ['blury']
                    #isDirty = True
                    # continue
                else:
                    print('Blur Value: %d, good'%blury_value)

                new_image_path = image_path.rsplit('.', 1)[0] + '_' + str(i) + '.' + EXT_IMG    #image_path.rsplit('.', 1)[1]
                misc.imsave(new_image_path, aligned)  # 保存为图像
                prewhitened = facenet.prewhiten(aligned)
                face_path[new_image_path] = prewhitened
                blury_arr[new_image_path] = blury_value
                imgs_style[new_image_path] = '|'.join(style)  # 如 'left_side|raise_head'
                if SAVE_FULL_BODY and result:
                    face_body[new_image_path] = file_path_to_save
                else:
                    face_body[new_image_path] = ''
                #isDirty_arr[new_image_path] = isDirty
                #print(prewhitened.shape)
        return face_path, imgs_style, blury_arr, face_body #, isDirty_arr , dlib_bb_dict
    return None, None, None, None #, None , None


def featureCalculation(imgpath):
    img = misc.imread(os.path.expanduser(imgpath))
    prewhitened = facenet.prewhiten(img)
    with graph.as_default():
        with sess.as_default():
            embedding = FaceProcessing.FaceProcessingImageData(prewhitened, sess, graph)[0]
    return embedding


def detectMotion(img_path,uuid):
    min_area = 200
    img_gray = cv2.imread(os.path.expanduser(img_path), 0)
    if uuid in preFrameOnDevice:
        frameDelta = cv2.absdiff(preFrameOnDevice[uuid], img_gray)
        preFrameOnDevice[uuid] = img_gray
        thresh = cv2.threshold(frameDelta, 25, 255, cv2.THRESH_BINARY)[1]
        (cnts, _) = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
        delta_value = 0
        for c in cnts:
            # if the contour is too small, ignore it
            delta_value+= cv2.contourArea(c)
        if delta_value >= min_area:
            #(x, y, w, h) = cv2.boundingRect(c)
            print(cv2.boundingRect(c))
            #cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            print('Moved delta %d'% delta_value)
            return True
        return False
    else:
        preFrameOnDevice[uuid] = img_gray
    return True


def updatePeopleImgURL(ownerid, url, embedding, uuid, objid, img_type, accuracy, fuzziness, sqlId, style, img_ts, tid,
                       p_ids,waiting):
    if len(url) < 1 or len(uuid) < 1 or len(objid) < 1 or len(img_type) < 1:
        return

    print(sqlId)
    if (img_type == 'object'):
        if not DO_NOT_REPORT_TO_SERVER:
            save2gst(uuid, objid, url, '', 'object', accuracy, int(fuzziness), 0, "", img_ts,tid,waiting)  # 发送请求给workai
        return

    # 换成迁移训练，不需要预生成这个数据
    # with app.app_context():
    #     man = People.query.filter_by(id=ownerid).first()
    #     man.aliyun_url = url
    #     db.session.add(man)
    #     db.session.commit()
    #
    #     train = TrainSet(url=url,
    #                      embed=embedding,
    #                      device_id=uuid,
    #                      face_id=ownerid)  # 系统自动label，生成一个训练数据
    #     db.session.add(train)
    #     db.session.commit()

    if not DO_NOT_REPORT_TO_SERVER:
        save2gst(uuid, objid, url, '', 'face', accuracy, int(fuzziness), int(sqlId), style, img_ts, tid, p_ids,waiting)  # 发送请求给workai


def compare(emb1, emb2):
    dist = np.sqrt(np.sum(np.square(np.subtract(emb1, emb2))))
    # d = emb1 - emb2
    # sqL2 = np.dot(d, d)

    # print("+ Squared l2 distance between representations: {:0.3f}, dist is {:0.3f}".format(sqL2,dist))
    # print("+ distance between representations:  {:0.3f}".format(dist))
    # return sqL2
    return dist

def compare2(emb1, emb2):
    dist = np.sum([emb2]*emb1, axis=1)
    return dist

def allowed_file(filename):
    """
    检查文件扩展名是否合法
    :param filename:
    :return: 合法 为 True
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

def check_accuracy(confident, val):
    c = int(confident*100)
    v = int(val*100)
    if v == c :
        return 0.10
    if v > c :
        return 0.01

    percent = (float(c) - float(v))/float(c)
    if (percent<0.10):
        percent = 0.49
    else:
        percent = percent + 0.50

    if (percent>=1.0):
        percent = 0.99

    percent = round(percent, 2)
    return percent

def blur_detection(img_path=None, img_buff=None):
    img = None

    if img_path is None and img_buff is None:
        return 1

    if img_buff is None:
        img = misc.imread(os.path.expanduser(img_path))
    else:
        img = img_buff

    gray_face = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blury_value = cv2.Laplacian(gray_face, cv2.CV_64F).var()
    print(">>> object blury_value: %d" %(blury_value))
    return blury_value

#
# 返回值:
#    found:  发现符合CONFIDENT_VALUE_THRESHOLD的记录
#    total:  遍历过这个人的记录
#
def check_embedding_on_detected_person(current_groupid, embedding, style, classid):
    total = 0
    found = 0
    people = None
    #遍历整个数据库, 检查这个人是谁
    if SVM_TRAIN_WITHOUT_CATEGORY is True:
        people = People.query.filter_by(group_id=current_groupid, classId=classid).all()
    else:
        people = People.query.filter_by(group_id=current_groupid, style=style, classId=classid).all()
    if people:
        for person in people:
            val = compare(embedding, person.embed)
            total = total+1
            face_accuracy = check_accuracy(confident_value, val)  # facenet计算的accuracy
            if face_accuracy >= CONFIDENT_VALUE_THRESHOLD:
                found = found+1
            if total >= 500:
                break
    return found, total

def check_embedding_on_detected_person_forSVM(current_groupid, embedding, style, classid):
    total = 0
    found = 0
    people = None
    #遍历整个数据库, 检查这个人是谁
    if SVM_TRAIN_WITHOUT_CATEGORY is True:
        people = People.query.filter_by(group_id=current_groupid, classId=classid).all()
    else:
        people = People.query.filter_by(group_id=current_groupid, style=style, classId=classid).all()
    if people:
        for person in people:
            val = compare2(embedding, person.embed)
            total = total+1
            #face_accuracy = check_accuracy(confident_value, val)  # facenet计算的accuracy
            face_accuracy = val
            print('face_accuracy={}'.format(face_accuracy))
            #if face_accuracy >= 0.55:
            if face_accuracy >= 0.70:
                found = found+1
            if total >= 500:
                break
    return found, total

#
# 返回值:
#    classId:  点圈里面人名字对应的ID，多个平板之间同一个人名字这个ID是相同的, 返回None 表示没有识别出这个人
#    sqlId:    与当前被检测embedding接近的那条数据的id, 即原始数据Id
#    accuracy: 点圈里面显示的匹配度
#
def find_nearest_embedding(current_groupid, uuid, embedding, style, peopleNum):
    if EN_SOFTMAX is True and SOFTMAX_ONLY is True:
        return None, None, None

    result_classId = {'Id': None, 'dist': None}

    #遍历整个数据库，检查这张图片不是人脸
    people = People.query.filter_by(group_id=current_groupid, classId="notface").all()
    if people:
        min_value = min([(compare(embedding, p.embed), p.objId, p.classId, p.id) for p in people])  # 遍历数据库并求最小compare值
        if min_value[0] < confident_value:
            face_accuracy = check_accuracy(confident_value, min_value[0])  # facenet计算的accuracy
            if face_accuracy > 0.9:
                print("this must be a None-face image")
                return min_value[2], min_value[3], face_accuracy

    #遍历整个数据库, 检查这个人是谁
    people = People.query.filter_by(group_id=current_groupid, style=style).all()
    if people:
        min_value = min([(compare(embedding, p.embed), p.objId, p.classId, p.id) for p in people if p.classId != "notface"])  # 遍历数据库并求最小compare值
        print(min_value)
        face_accuracy = check_accuracy(confident_value, min_value[0])  # facenet计算的accuracy
        if face_accuracy >= CONFIDENT_VALUE_THRESHOLD:
            result_classId['Id'] = min_value[2]
            result_classId['dist'] = min_value[0]
            face_accuracy = check_accuracy(confident_value, min_value[0])  # facenet计算的accuracy
            print(">>> same people(db): accuracy=%f" % (face_accuracy))
            return result_classId['Id'], min_value[3], face_accuracy

    return None, None, None

def insertOneImageIntoPeopleDB(filepath, uuid, group_id, objid, url, notFace=False, style="front"):
    if notFace is True:
        classId = "notface"
    else:
        classId = objid

    if not os.path.exists(filepath):
        print("file not exists %s" %(filepath))
        return
    embedding = featureCalculation(filepath)
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
                    aligned = misc.imresize(img, (image_size, image_size))
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

def autogroupThreadSubFunc(facial_encodings, unknownImages_array):
    print("autogroupThreadSubFunc: len(unknownImages_array)={}".format(len(unknownImages_array)))
    current_order_list = OrderedDict()
    for item in unknownImages_array:
        current_order_list[item["url"]] = item["face_id"], item["filepath"]
    start_time = time.time()
    #unknown_length = len(unknownImages_array)
    current_groupid = get_current_groupid()
    device_id = get_deviceid()
    people = AutoGroupSet.query.filter_by(group_id=current_groupid, style="front").all()
    print("len(people)={}".format(len(people)))
    if people:
        for person in people:
            #facial_encodings[getFacialImagePath(person.filepath)] = person.embed
            #print("person.url={}, person.embed={}".format(person.url, person.embed))
            #numpy.ndarray
            facial_encodings[person.url] = person.face_id, person.embed
            #print("type(person.embed)={}".format(type(person.embed)))
            #print("person.embed={}".format(person.embed))
            current_order_list[person.url] = person.face_id, person.filepath
    print("current_order_list = {}".format(current_order_list))
    #print("facial_encodings={}".format(facial_encodings))
    print("autogroupThreadSubFunc get facial encodings costs {} S".format(time.time() - start_time))
    #sendMessage2Group(device_id, toid, '-> Train cost {}s'.format(time.time() - start_time))
    print("facial_encodings={}".format(facial_encodings))
    results = clustering_people.cluster_unknown_people(facial_encodings, current_order_list)
    json_string = "{}devId:{}, group_id:{}, results:{}{}".format('{', device_id, current_groupid, results, '}')
    json_dict = {"devId":device_id, "group_id":current_groupid, "results":results}
    mqttc.publish("/msg/autogroup/{}".format(current_groupid), json.dumps(json_dict))

def autogroupThreadFunc():
    global AutogroupDB
    global AutogroupDatasetDB
    global isSyncAutogroupDataset
    global isStartAutogroup

    unknown_faceId = "unknown"
    while True:
        try:
            if isSyncAutogroupDataset is True:
                if not syncAutogroupDatasetFunc():
                    time.sleep(6)
                    continue
                isSyncAutogroupDataset = False

            datasetDic = []
            if AutogroupDatasetDB is not None:
                datasetDic = AutogroupDatasetDB.fetch()
            if (len(datasetDic) > 0):
                print("len(AutogroupDatasetDB)={}".format(len(datasetDic)))
                print("autogroupThreadFunc: download dataset %d" % len(datasetDic))
                for key in datasetDic:
                    print("key = {}".format(key))
                    info = datasetDic[key]
                    #if SVM_TRAIN_WITHOUT_CATEGORY is True:
                    #    info['style'] = 'front'
                    print("info = {}".format(info))
                    ret = urllib2.urlopen(info['url'])
                    if ret.code != 200:
                        AutogroupDatasetDB.remove(key)
                        print("URL{} not exists, continue.".format(info['url']))
                    print("info['url'] = {}".format(info['url']))
                    img_path = save_embedding.get_image_path_dst(info['url'], info['group_id'], info['face_id'], info['style'], "autogroup")
                    print("img_path = {}".format(img_path))
                    embedding_path = save_embedding.get_embedding_path(img_path)
                    embedding = None
                    if not os.path.exists(img_path):
                        img_path = save_embedding.download_img_for_svm_dst(info['url'], info['group_id'], info['face_id'], info['style'], "autogroup")
                    if img_path:
                        if not os.path.exists(embedding_path):
                            img = misc.imread(os.path.expanduser(img_path))  # 手动裁剪后的图片需要再缩放一下
                            aligned = misc.imresize(img, (image_size, image_size))
                            misc.imsave(img_path, aligned)
                            embedding = featureCalculation(img_path)
                            embedding_path = save_embedding.get_embedding_path(img_path)
                            save_embedding.create_embedding_string(embedding, embedding_path)
                        old_autogroup_set = AutoGroupSet.query.filter_by(url=info['url'], group_id=info['group_id'], is_or_isnot=True, style=info['style']).first()
                        if not old_autogroup_set:
                            if embedding is None:
                                embedding_path = save_embedding.get_embedding_path(img_path)
                                embedding = save_embedding.read_embedding_string(embedding_path)
                                embedding = np.asarray(embedding)
                            unique_face_id = info['unique_face_id'] if unique_face_id in info else ''
                            autoGroupSet = AutoGroupSet(url=info['url'], group_id=info['group_id'], is_or_isnot=True,
                                             device_id=info['device_id'], face_id=info['face_id'], unique_face_id=unique_face_id, style=info['style'], filepath=img_path, embed=embedding)
                            db.session.add(autoGroupSet)
                            db.session.commit()
                            print('-> autogroupThreadFunc downloaded url {} to {}'.format(info['url'], img_path))
                    AutogroupDatasetDB.remove(key)

            datasetDic = []
            if AutogroupDB is not None:
                datasetDic = AutogroupDB.fetch()
            if isStartAutogroup is True:
                facial_encodings = OrderedDict()
                if (len(datasetDic) > 0):
                    print("len(AutogroupDB)={}".format(len(datasetDic)))
                    print("autogroupThreadFunc: download Autogroup data %d" % len(datasetDic))
                    unknownImages_array = []
                    for key in datasetDic:
                        info = datasetDic[key]
                        if 'url' not in info or 'group_id' not in info or 'face_id' not in info:
                            print("Missing key information in message.")
                            continue
                        ret = urllib2.urlopen(info['url'])
                        if ret.code != 200:
                            AutogroupDB.remove(key)
                            print("URL{} not exists, continue.".format(info['url']))
                        img_path = save_embedding.get_image_path_dst(info['url'], info['group_id'], unknown_faceId, info['style'], "autogroup")
                        embedding_path = save_embedding.get_embedding_path(img_path)
                        basepath = os.path.abspath(os.getenv('RUNTIME_BASEDIR',os.path.dirname(__file__)))
                        local_path = os.path.join(basepath, "face_testdataset/" + info['group_id']+"/noname/"+os.path.basename(info['url']))
                        print("local_path = {}".format(local_path))
                        if os.path.exists(local_path):
                            shutil.copy(local_path, img_path)
                            print("Copied local file {} to {}".format(local_path, img_path))
                        if not os.path.exists(img_path):
                            img_path = save_embedding.download_img_for_svm_dst(info['url'], info['group_id'], unknown_faceId, info['style'], "autogroup")
                        if img_path:
                            if not os.path.exists(embedding_path):
                                img = misc.imread(os.path.expanduser(img_path))  # 手动裁剪后的图片需要再缩放一下
                                aligned = misc.imresize(img, (image_size, image_size))
                                misc.imsave(img_path, aligned)
                                embedding = featureCalculation(img_path)
                                embedding_path = save_embedding.get_embedding_path(img_path)
                                save_embedding.create_embedding_string(embedding, embedding_path)
                                #AutoGroupEmbeddings.append({info['url']: embedding})
                                #facial_encodings[getFacialImagePath(img_path)] = embedding
                            else:
                                embedding_path = save_embedding.get_embedding_path(img_path)
                                embedding = save_embedding.read_embedding_string(embedding_path)
                            #list
                            facial_encodings[info['url']] = unknown_faceId, np.asarray(embedding)
                            print("type(embedding) = {}".format(type(embedding)))
                            unknownImages_array.append({"filepath":img_path, "url":info['url'], "face_id":unknown_faceId, "style":info['style']})
                        AutogroupDB.remove(key)
                    print("len(facial_encodings)={}".format(len(facial_encodings)))
                if len(facial_encodings) > 0:
                    #TODO compare facial
                    autogroupThreadSubFunc(facial_encodings, unknownImages_array)
                else:
                    autogroupThreadSubFunc(facial_encodings, [])
                isStartAutogroup = False

        except Exception as ex:
            print('autogroupThreadFunc: except:', ex)
            isSyncAutogroupDataset = False
            isStartAutogroup = False

        time.sleep(6)

autogroupThread = threading.Thread(target=autogroupThreadFunc)
autogroupThread.daemon = True
#autogroupThread.start()


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

                #status, embedding = down_img_embedding(img_url, group_id, faceid, style=style)
                img_path = save_embedding.get_image_path(img_url, group_id, faceId, style)
                #print("img_path = {}".format(img_path))
                embedding_path = save_embedding.get_embedding_path(img_path)
                embedding = None
                if not os.path.exists(img_path):
                    img_path = save_embedding.download_img_for_svm(img_url, group_id, faceId, style)
                if img_path:
                    if not os.path.exists(embedding_path):
                        img = misc.imread(os.path.expanduser(img_path))  # 手动裁剪后的图片需要再缩放一下
                        aligned = misc.imresize(img, (image_size, image_size))
                        misc.imsave(img_path, aligned)
                        embedding = featureCalculation(img_path)
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
                        print("We have tried 3 times to download the autogroup dataset.")
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
                            del urlsInLocalDB[item]
                urlsTemp = None
                print("Trainsets: 2, len(urlsInLocalDB) = {}".format(len(urlsInLocalDB)))
                print("Trainsets: 2, len(urlsOnServer) = {}".format(len(urlsOnServer)))

                #Remove invalid photos from local
                dataset = []
                style = ''
                if SVM_TRAIN_WITHOUT_CATEGORY is True:
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
                    message = 'Stat: localDB={}, server={}, localfiles={}'.format(len(urlsInLocalDB), len(urlsOnServer), len(dataset)-willRemoveCount)
                    print(message)
                    sendMessage2Group(device_id, toid, message)
                return True
            else:
                print('response code != 200')
                return False
    except Exception as ex:
        print('disposeFinalSyncDatasetsThreadFunc: except:', ex)

def disposeSyncStatusInfoThreadFunc(device_id, toid):
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
                        urlsOnServer[img_url] = group_id, faceId, style
                print("Trainsets: len(urlsInLocalDB) = {}".format(len(urlsInLocalDB)))
                print("Trainsets: len(urlsOnServer) = {}".format(len(urlsOnServer)))

                #Remove invalid photos from local
                dataset = []
                style = ''
                if SVM_TRAIN_WITHOUT_CATEGORY is True:
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
                    message = 'StatInfo: localDB={}, server={}, localfiles={}'.format(len(urlsInLocalDB), len(urlsOnServer), len(dataset))
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

def get_empty_faceid(current_groupid, uuid, embedding,
                  img_style, number_people, img_objid, forecast_result):
    """
    当softmax无结果时（无模型/预测置信度低）调用遍历数据库识别
    :param current_groupid:
    :param uuid:
    :param embedding:
    :param img_style:
    :param number_people:
    :param img_objid:
    :return:
    """
    json_data = {'detected': True, 'recognized': False}
    face_id = img_objid + str(all_face_index).zfill(4)

    json_data['recognized'] = False
    json_data['face_id'] = face_id
    json_data['accuracy'] = 0
    json_data['style'] = img_style

    forecast_result['face_id'] = face_id
    forecast_result['face_accuracy'] = 0
    embedding_string = ','.join(str(x) for x in embedding)
    forecast_result['embedding_string'] = embedding_string
    return json_data, forecast_result

def use_db_detect(current_groupid, uuid, embedding,
                  img_style, number_people, img_objid, forecast_result):
    """
    当softmax无结果时（无模型/预测置信度低）调用遍历数据库识别
    :param current_groupid:
    :param uuid:
    :param embedding:
    :param img_style:
    :param number_people:
    :param img_objid:
    :return:
    """
    json_data = {'detected': True, 'recognized': False}
    face_id, sqlId, face_accuracy = find_nearest_embedding(current_groupid, uuid, embedding, img_style,
                                                           number_people)
    if face_id is not None:
        print(">>> same people: accuracy=%f" % (face_accuracy))
        people = None
        people_sqlId = sqlId

        json_data['recognized'] = True
        json_data['face_id'] = face_id
        json_data['accuracy'] = int(face_accuracy * 100)
        forecast_result['face_accuracy'] = face_accuracy
    else:
        face_id = img_objid + str(all_face_index).zfill(4)

        people = People(embed=embedding, uuid=uuid, group_id=current_groupid,
                        objId=face_id, aliyun_url='', classId=face_id, style=img_style)
        db.session.add(people)
        db.session.commit()
        people_sqlId = people.id
        print(">>> new people")
        json_data['recognized'] = False
        json_data['face_id'] = face_id
        json_data['accuracy'] = 0

    forecast_result['people'] = people
    forecast_result['people_sqlId'] = people_sqlId
    forecast_result['face_id'] = face_id
    forecast_result['face_accuracy'] = face_accuracy
    return json_data, forecast_result


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


def upload_forecast_result(key, forecast_result, json_data, num_p):
    uuid = forecast_result['uuid']
    face_id = forecast_result['face_id']
    face_accuracy = forecast_result['face_accuracy']
    people_sqlId = forecast_result['people_sqlId']
    align_image_path = forecast_result['align_image_path']
    img_style_str = forecast_result['img_style_str']
    ts = forecast_result['ts']
    trackerId = forecast_result['trackerId']
    face_fuzziness = forecast_result['face_fuzziness']
    people = forecast_result['people']
    p_ids = forecast_result['p_ids']
    embedding_string = forecast_result['embedding_string']
    embedding_bytes = embedding_string.encode('utf-8')
    img_type = forecast_result['img_type']
    waiting = forecast_result['waiting']
    do_not_report_to_server = DO_NOT_REPORT_TO_SERVER
    uploadedimgurl = None

    if img_type is not None and img_type == 'body':
        do_not_report_to_server = True

    if face_id is not None and face_id != "notface":
        embedding_url = qiniu_upload_data(key, embedding_bytes)
        uploadedimgurl = uploadImg.uploadImage(key, 'notownerid', align_image_path,
                                               embedding='', uuid=uuid,
                                               block=False, DO_NOT_REPORT_TO_SERVER=do_not_report_to_server,
                                               objid=face_id, img_type=img_type,
                                               accuracy=face_accuracy, fuzziness=face_fuzziness, sqlId=people_sqlId,
                                               style=img_style_str, ts=ts, tid=str(trackerId), p_ids=p_ids, waiting = waiting)
    # if uploadedimgurl is not None:
    #     forecast_result['url'] = uploadedimgurl
    #     forecast_result['detected'] = json_data['detected']
    #     push_or_not = push_resultQueue(forecast_result, num_p)
    return uploadedimgurl
        # print(align_image_path)
        # if os.path.exists(align_image_path):
        #    os.remove(align_image_path)


def sendDebugLogToGroup(uuid, current_groupid, message):
    if ENABLE_DEBUG_LOG_TO_GROUP is True:
        sendMessage2Group(uuid, current_groupid, message)
def SVM_classifier(embedding,align_image_path,uuid,current_groupid,img_style,number_people, img_objid,json_data, forecast_result):
    #Save image to src/face_dataset_classify/group/person/
    if SVM_SAVE_TEST_DATASET is True:
        group_path = os.path.join(svm_face_testdataset, current_groupid)
        if not os.path.exists(group_path):
            os.mkdir(group_path)
        print('test dataset group_path=%s' % group_path)

    pkl_path = ""
    if SVM_TRAIN_WITHOUT_CATEGORY is True:
        pkl_path = 'faces/{}/{}/classifier_182.pkl'.format(current_groupid, 'front')
    else:
        pkl_path = 'faces/{}/{}/classifier_182.pkl'.format(current_groupid, img_style)
    svm_detected = False

    if os.path.exists(pkl_path):
        tmp_image_path = 'faces/noname/person/face_tmp.'+EXT_IMG
        shutil.copyfile(align_image_path, tmp_image_path)

        # 输入embedding的预测方法, 速度很快
        svm_stime = time.time()
        _, human_string, score, top_three_name = classifier_classify_new.classify(embedding, pkl_path)
        if top_three_name:
            top_three_faceid = [name.split(' ')[1] for name in top_three_name]
        else:
            top_three_faceid = None

        print('-> svm classify cost {}s'.format(time.time()-svm_stime))
        if human_string is not None:
            message = ""
            message2 = ""
            face_id = human_string.split(' ')[1]
            score = round(score, 2)
            fuzziness = forecast_result['face_fuzziness']

            '''
            if score >= 0.85:
                if SVM_HIGH_SCORE_WITH_DB_CHECK is False:
                    svm_detected = True
                message = "<SVM Recognized> Face ID: %s %s/%s" % (face_id, score, img_style)
                if SVM_HIGH_SCORE_WITH_DB_CHECK is True:
                    found, total = check_embedding_on_detected_person_forSVM(current_groupid=current_groupid,
                                   embedding=embedding,style=img_style,classid=face_id)
                    if (total>=30 and found>1) or (total<30 and found>0):
                        svm_detected = True
                        message2 = "<DB Recognized> Face ID: %s %s/%s, 2nd %s/%s" % (face_id, score, img_style, found, total)
                    else:
                        message2 = "<DB 3nd Score Low> Face ID: %s %s/%s, 2nd %s/%s" % (face_id, score, img_style, found, total)
            elif
            '''
            if score >= 0.93 or (score > 0.80 and fuzziness > 90):
                found, total = check_embedding_on_detected_person_forSVM(current_groupid=current_groupid,
                               embedding=embedding,style=img_style,classid=face_id)
                if found > 0:
                    svm_detected = True
                    message = "<DB Recognized> Face ID: %s %s/%s, 2nd %s/%s" % (face_id, score, img_style, found, total)
                else:
                    message = "<DB 2nd Score Low> Face ID: %s %s/%s, 2nd %s/%s" % (face_id, score, img_style, found, total)
            elif 0.35<score<0.8:
                message = "Send this face to Zone Waiting: %s,%s"%(score, fuzziness)
                forecast_result['waiting'] = True
            else:
                message = "<1st Score Low> Face ID: %s %s/%s" % (face_id, score, img_style)

            print(message)
            if (message2 != ""):
                print(message2)
            if svm_detected is True:
                json_data['recognized'] = True
                json_data['face_id'] = face_id
                json_data['accuracy'] = int(score*100)
                json_data['style'] = img_style

                forecast_result['face_id'] = face_id
                forecast_result['face_accuracy'] = score
                embedding_string = ','.join(str(x) for x in embedding)
                forecast_result['embedding_string'] = embedding_string
            else:
                forecast_result['p_ids'] = top_three_faceid
                print("Not Recognized %s" % face_id)
            sendDebugLogToGroup(uuid, current_groupid, message)
            #Save image to src/face_dataset_classify/group/person/
    if SVM_SAVE_TEST_DATASET is True:
        if svm_detected is True:
            svm_face_testdataset_person_path = os.path.join(group_path, human_string)
        else:
            svm_face_testdataset_person_path = os.path.join(group_path, 'noname')

        if not os.path.exists(svm_face_testdataset_person_path):
            os.mkdir(svm_face_testdataset_person_path)
        print('test dataset person path=%s' % svm_face_testdataset_person_path)
        dir = os.path.basename(align_image_path)
        name = os.path.splitext(dir)[0]
        save_testdataset_filepath = os.path.join(svm_face_testdataset_person_path, name+'_'+str(int(time.time()))+'.png')
        print('save classified image to path: %s' % save_testdataset_filepath)
        shutil.copyfile(align_image_path, save_testdataset_filepath)
    if svm_detected is False:
        json_data, forecast_result = get_empty_faceid(current_groupid, uuid, embedding,
                                                    img_style, number_people, img_objid,
                                                    forecast_result)
        print('not in train classification or need to more train_dataset')

    return json_data, forecast_result

def SVM_classifier_stranger(embedding,align_image_path,uuid,current_groupid,img_style,number_people, img_objid,json_data, forecast_result):
    #Save image to src/face_dataset_classify/group/person/
    if SVM_SAVE_TEST_DATASET is True:
        group_path = os.path.join(svm_stranger_testdataset, current_groupid)
        if not os.path.exists(group_path):
            os.mkdir(group_path)
        print('test dataset group_path=%s' % group_path)

    pkl_path = ""
    if SVM_TRAIN_WITHOUT_CATEGORY is True:
        pkl_path = 'faces/{}/{}/classifier_182.pkl'.format(current_groupid, 'front')
    else:
        pkl_path = 'faces/{}/{}/classifier_182.pkl'.format(current_groupid, img_style)
    svm_detected = False

    if os.path.exists(pkl_path):
        tmp_image_path = 'faces/noname/person/face_tmp.'+EXT_IMG
        shutil.copyfile(align_image_path, tmp_image_path)

        # 输入embedding的预测方法, 速度很快
        svm_stime = time.time()
        _, human_string, score, top_three_name = classifier_classify_new.classify(embedding, pkl_path)
        if top_three_name:
            top_three_faceid = [name.split(' ')[1] for name in top_three_name]
        else:
            top_three_faceid = None

        print('-> svm classify cost {}s'.format(time.time()-svm_stime))
        if human_string is not None:
            message = ""
            message2 = ""
            face_id = human_string.split(' ')[1]
            score = round(score, 2)

            '''
            if score >= 0.85:
                if SVM_HIGH_SCORE_WITH_DB_CHECK is False:
                    svm_detected = True
                message = "<SVM Recognized> Face ID: %s %s/%s" % (face_id, score, img_style)
                if SVM_HIGH_SCORE_WITH_DB_CHECK is True:
                    found, total = check_embedding_on_detected_person_forSVM(current_groupid=current_groupid,
                                   embedding=embedding,style=img_style,classid=face_id)
                    if (total>=30 and found>1) or (total<30 and found>0):
                        svm_detected = True
                        message2 = "<DB Recognized> Face ID: %s %s/%s, 2nd %s/%s" % (face_id, score, img_style, found, total)
                    else:
                        message2 = "<DB 3nd Score Low> Face ID: %s %s/%s, 2nd %s/%s" % (face_id, score, img_style, found, total)
            elif
            '''
            if score >= 0.35:
                found, total = check_embedding_on_detected_person_forSVM(current_groupid=current_groupid,
                               embedding=embedding,style=img_style,classid=face_id)
                if found > 0:
                    svm_detected = True
                    message = "<DB Recognized> Face ID: %s %s/%s, 2nd %s/%s" % (face_id, score, img_style, found, total)
                else:
                    message = "<DB 2nd Score Low> Face ID: %s %s/%s, 2nd %s/%s" % (face_id, score, img_style, found, total)
            else:
                message = "<1st Score Low> Face ID: %s %s/%s" % (face_id, score, img_style)

            print(message)
            if (message2 != ""):
                print(message2)
            if svm_detected is True:
                json_data['recognized'] = True
                json_data['face_id'] = face_id
                json_data['accuracy'] = int(score*100)
                json_data['style'] = img_style

                forecast_result['face_id'] = face_id
                forecast_result['face_accuracy'] = score
                embedding_string = ','.join(str(x) for x in embedding)
                forecast_result['embedding_string'] = embedding_string
            else:
                forecast_result['p_ids'] = top_three_faceid
                print("Not Recognized %s" % face_id)
            sendDebugLogToGroup(uuid, current_groupid, message)
            #Save image to src/face_dataset_classify/group/person/
    if SVM_SAVE_TEST_DATASET is True:
        if svm_detected is True:
            svm_face_testdataset_person_path = os.path.join(group_path, human_string)
        else:
            svm_face_testdataset_person_path = os.path.join(group_path, 'noname')

        if not os.path.exists(svm_face_testdataset_person_path):
            os.mkdir(svm_face_testdataset_person_path)
        print('test dataset person path=%s' % svm_face_testdataset_person_path)
        dir = os.path.basename(align_image_path)
        name = os.path.splitext(dir)[0]
        save_testdataset_filepath = os.path.join(svm_face_testdataset_person_path, name+'_'+str(int(time.time()))+'.png')
        print('save classified image to path: %s' % save_testdataset_filepath)
        shutil.copyfile(align_image_path, save_testdataset_filepath)
    if svm_detected is False:
        json_data, forecast_result = get_empty_faceid(current_groupid, uuid, embedding,
                                                    img_style, number_people, img_objid,
                                                    forecast_result)
        print('not in train classification or need to more train_dataset')

    return json_data, forecast_result

def SoftMax_classifier(embedding,align_image_path,uuid,current_groupid,img_style,number_people, img_objid,json_data, forecast_result):
    tmp_image_path = 'faces/face_tmp.jpg'
    shutil.copyfile(align_image_path, tmp_image_path)

    embedding_path = tmp_image_path + '.txt'
    save_embedding.create_embedding_string(embedding, embedding_path)
    score, human_string, fraction = test_on_embedding.test_on_bottleneck(embedding_path, current_groupid, img_style)

    face_id = human_string.split('_')[1]
    if fraction > 0.88 and face_id not in ['Bachan', 'dmz', 'dq', 'Rodriguez', 'jyt', 'lj', 'lq', 'lqd', 'sbn', 'wsc', 'xdd', 'ylp']:
        face_accuracy = round(fraction, 2)
        # print(human_string)
        print(">>> this is: %s  score:%s and fraction: %s" % (face_id, score, fraction))
        people = People(embed=embedding, uuid=uuid, group_id=current_groupid,
                        objId=face_id, aliyun_url='', classId=face_id, style=img_style)
        db.session.add(people)
        db.session.commit()

        json_data['recognized'] = True
        json_data['face_id'] = face_id
        json_data['accuracy'] = int(fraction*100)

        forecast_result['face_id'] = face_id
        forecast_result['face_accuracy'] = face_accuracy
    else:
        print('not in train classification or need to more train_dataset')
        json_data, forecast_result = use_db_detect(current_groupid, uuid, embedding,
                                                    img_style,number_people,img_objid,
                                                    forecast_result)
    return json_data, forecast_result


def Mobilenet_classifier(body_path,current_groupid, body_result):
    score, human_string, fraction = predict(body_path, current_groupid)


    face_id = human_string.split(' ')[1]
    face_accuracy = round(score, 2)
    # print(human_string)
    print(">>> this body is: %s  score:%s and fraction: %s" % (face_id, score, fraction))

    body_result['face_id'] = face_id
    body_result['face_accuracy'] = face_accuracy

    return body_result


def mobilenet_labeled_download(url, group_id, face_id):
    body_url = url + '_body'
    body_bottleneck_url = body_url + SUFFIX
    body_path = download_img_for_body(body_url, group_id, face_id, style=None)
    # if body_path:
    #     bottleneck_path = get_embedding_path_for_body(body_path)
    #     status = down_embedding_for_body(body_bottleneck_url, bottleneck_path)
    #     if not status:
    #         # 下载embedding失败， 开始计算embedding
    #         mobilenet.single_create_bottleneck_file(body_path, bottleneck_path)

def face_recognition_on_face_image(img_data,blury_arr,uuid,
                                   current_groupid,imgs_style,trackerId,
                                   timestamp1,ts, body_data):
    global all_face_index
    img_objid = trackerId
    print("img_objid = {}".format(img_objid))
    number_people = 1
    for align_image_path, prewhitened in img_data.items():
        print("number of people=%d" % (number_people))
        if number_people > 1:
            trackerId = str(uuid1())
        number_people += 1
        img_style_str = imgs_style[align_image_path]
        img_style = img_style_str
        json_data = {'detected':False, 'recognized': False, 'style': img_style_str}

        forecast_result = {'people':None,
                         'img_type': 'face',
                         'people_sqlId': 0,
                         'face_id': None,  # 当前这个人脸图片的objId/face_id
                         'trackerId': trackerId,
                         'uuid': uuid,
                         'ts': ts,
                         'img_style_str': img_style_str,
                         'align_image_path': align_image_path,
                         'face_accuracy': 0,
                         'face_fuzziness': 0,
                         'embedding_string': '',
                         'p_ids': None,
                         }  # 保存发送给uploadImage的数据
        if SAVE_FULL_BODY:
            body_path = body_data[align_image_path]
            body_result = {'people':None,
                             'img_type': 'body',
                             'people_sqlId': 0,
                             'face_id': None,  # 当前这个人脸图片的objId/face_id
                             'trackerId': trackerId,
                             'uuid': uuid,
                             'ts': ts,
                             'img_style_str': img_style_str,
                             'align_image_path': body_path,
                             'face_accuracy': 0,
                             'face_fuzziness': 0,
                             'embedding_string': '',
                             'p_ids': None,
                             }

            if body_path:
                # 检查开关及人体图是否存在
                # bottleneck_values = mobilenet.run_bottleneck(body_path)
                # bottleneck_string = ','.join(str(x) for x in bottleneck_values)
                # body_result['embedding_string'] = bottleneck_string
                if os.path.isfile('Mobilenet/{}/bottlenecks_graph.pb'.format(current_groupid)):
                    body_result = Mobilenet_classifier(body_path, current_groupid, body_result)

        if NEAR_FRONTIAL_ONLY is True:
            if not img_style == 'front':
                message = "<Side Face> Skip non-near-frontial image[%s]" % (img_style)
                print(message)

                json_data, forecast_result = get_empty_faceid(current_groupid, uuid, '',
                                                            img_style, number_people, img_objid,
                                                            forecast_result)

                key = str(uuid1())
                if not DO_NOT_UPLOAD_IMAGE:
                    upload_forecast_result(key, forecast_result, json_data, number_people)
                if SAVE_FULL_BODY and body_path:
                    key += '_body'  # 表示人体
                    body_result['face_id'] = forecast_result['face_id'] + '_body'
                    upload_forecast_result(key, body_result, json_data,number_people)
                sendDebugLogToGroup(uuid, current_groupid, message)
                continue
        # 2个不认识的人同时出现在图片里面的时候用来生成不一样的face_id
        if all_face_index < 9999:
            all_face_index += 1
        else:
            all_face_index = 0

        if blury_arr[align_image_path] is not None:
            forecast_result['face_fuzziness'] = blury_arr[align_image_path]
            print(">>> blury=%d" %(blury_arr[align_image_path]))
        json_data['detected'] = True
        with graph.as_default():
            with sess.as_default():
                embedding = FaceProcessing.FaceProcessingImageData(prewhitened, sess, graph)[0]

        print("2 %.2f seconds" % (time.time() - timestamp1))
        if forecast_result['face_fuzziness'] < BLURY_THREHOLD:
            json_data, forecast_result = get_empty_faceid(current_groupid, uuid, embedding,
                                                    img_style, number_people, img_objid,
                                                    forecast_result)
            print("Too blurry image, skip it img_objid={}, trackerId={}".format(img_objid, trackerId))
        elif SVM_CLASSIFIER_ENABLED is True:
            #img_style = 'front'
            # embedding = embedding.reshape((1, -1))
            forecast_result['waiting'] = False
            json_data, forecast_result = SVM_classifier(embedding,align_image_path,
                uuid,current_groupid,img_style,number_people,img_objid,json_data,forecast_result)
        elif EN_SOFTMAX is True and os.path.isfile('faces/{}/{}/embedding_graph.pb'.format(current_groupid, img_style)):
            json_data, forecast_result = SoftMax_classifier(embedding,align_image_path,
                uuid,current_groupid,img_style,number_people,trackerId,json_data,forecast_result)
        else:
            print('Skip SoftMax/SVM')
            json_data, forecast_result = use_db_detect(current_groupid, uuid, embedding,
                                                        img_style, number_people, trackerId,
                                                        forecast_result)

        print("3 %.2f seconds" % (time.time() - timestamp1))


        # face cannot be recognized, process it as a stranger
        if json_data['recognized'] is False:
            json_data, forecast_result = SVM_classifier_stranger(embedding,align_image_path,
                uuid,current_groupid,img_style,number_people,img_objid,json_data,forecast_result)


        forecast_result['trackerId'] = trackerId
        # 人脸预测结果发送
        key = str(uuid1())

        # upload_forecast_result(key, forecast_result, json_data, number_people)
        face_id = forecast_result['face_id']
        if not DO_NOT_UPLOAD_IMAGE and face_id is not None and face_id != "notface":
            print("---------------------------UPLOAD----------------------------")
            push_or_not = push_resultQueue(forecast_result, number_people)
            if push_or_not is True:
                url = upload_forecast_result(key, forecast_result, json_data, number_people)
               # add stranger into Strange db
                # if forecast_result['recognized'] is False:
                #     with app.app_context():
                #         stranger = Stranger(embed=embedding, uuid=uuid, group_id=current_groupid, objId=face_id, aliyun_url=url,classId=face_id,style=style)
                #         db.session.add(stranger)
                #         db.session.commit

                # if url is not None:
                #    forecast_result['url'] = url
                #    forecast_result['detected'] = json_data['detected']

        if SAVE_FULL_BODY and body_path:
           key += '_body'  # 表示人体
           body_result['face_id'] = forecast_result['face_id'] + '_body'
           upload_forecast_result(key, body_result, json_data, number_people)

    #if os.path.exists(image_path):
    #    os.remove(image_path)
    #if os.path.exists(img_local_path):
    #    os.remove(img_local_path)

    resp = Response(json.dumps(json_data), status=200, mimetype='application/json')
    return resp

@app.route('/api/detect_face/', methods=['GET'])
def detect_face():
    return Response(json.dumps(get_resultQueue()), status=200, mimetype='application/json')

@app.route('/api/imgpath/', methods=['POST'])
@app.route('/api/fullimg/', methods=['POST'])
def upload_full_img():
    if request.files:
        f = request.files['file']
    else:
        f = None
    img_local_path = request.form.get('imgpath', '')
    print('img_local_path = %s' % (img_local_path))

    if f is None and img_local_path is None:
        print('f is None or img_local_path is None')
        return jsonify({'error': 1001, 'message': u'上传失败', "detected": False, "recognized": False})

    img_objid = trackerId = request.args.get('objid', '')  # 当前整张图片对应的objid/trackerId
    print('img_objid = %s' % (img_objid))
    current_groupid = get_current_groupid()

    #新平板没有添加到任何组，后面的处理会报错
    if current_groupid is None:
        return jsonify({"error": 1002, "message": u"平板没有添加组", "detected": False, "recognized": False})

    if f and allowed_file(f.filename):
        old_filename = f.filename
        new_filename, uuid, ts = format_img_filename(old_filename)
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], new_filename)
        f.save(image_path)
        print('image_path = %s' % (image_path))
    else:
        old_filename = os.path.basename(img_local_path)
        new_filename, uuid, ts = format_img_filename(old_filename)
        image_path = os.path.join(os.path.dirname(img_local_path), new_filename)
        print(img_local_path, image_path)
        os.rename(img_local_path, image_path)  # 加上 gFlask_port 后 rename

    print('-----------------------')
    timestamp1 = time.time()
    #print("0 %.2f seconds" % (time.time() - timestamp1))
    if FACE_DETECTION_WITH_DLIB is False:
        img_data, imgs_style, blury_arr, body_data = load_align_image(image_path, sess, graph, pnet, rnet, onet)
    else:
        img_data, blury_arr = dlibImageProcessor(image_path)
    print("1 %.2f seconds" % (time.time() - timestamp1))
    if img_data:
        if SAVE_ORIGINAL_FACE:
            shutil.copy(image_path, original_face_img_path)
        resp = face_recognition_on_face_image(img_data, blury_arr,uuid,
                                       current_groupid,imgs_style,img_objid,
                                       timestamp1,ts, body_data)

        #FIXME: 来回重命名文件应该没必要？
        if f is None and os.path.exists(image_path):
            os.rename(image_path, img_local_path)
        return resp
    else:
        print('No availabel face in this image')
        print('-----------------------')
        if EN_OBJECT_DETECTION is False:
            #if os.path.exists(image_path):
            #    os.remove(image_path)
            #if os.path.exists(img_local_path):
            #    os.remove(img_local_path)
            if f is None and os.path.exists(image_path):
                os.rename(image_path,img_local_path)
            return Response(json.dumps({"result": "ok", "detected": False, "recognized": False}),
                            status=200, mimetype='application/json')
        print("-- 2 %.2f seconds" % (time.time() - timestamp1))
        if img_objid:
            obj_accuracy = None
            obj_fuzziness = blur_detection(img_path=image_path)

            if os.path.isfile('objects/{}/bottlenecks_graph.pb'.format(current_groupid)):
                tmp_image_path = 'objects/tmp.jpg'
                bottleneck_path = tmp_image_path + '.txt'
                shutil.copyfile(image_path, tmp_image_path)
                gbottlenecks.single_create_bottleneck_file(image_path=tmp_image_path,
                                              bottleneck_path=bottleneck_path)
                score, human_string, fraction = test_on_bottleneck(bottleneck_path, current_groupid)
                if fraction > 0.85:
                    obj_accuracy = round(fraction, 2)
                    objId = human_string.split('_')[1]
            else:
                print('Bottlenecks_graph.pb not exist.')
            key = str(uuid1())
            imgurl = uploadImg.uploadImage(key, "notownerid", image_path,
                                  embedding="notembedding", uuid=uuid,
                                  block=False, DO_NOT_REPORT_TO_SERVER=False, objid=objId, img_type='object',
                                  accuracy=obj_accuracy, fuzziness=int(obj_fuzziness), sqlId=0, ts=ts, tid=str(trackerId)
                                  )

            return Response(json.dumps({"result":"ok"}), status=200, mimetype='application/json')

        #if os.path.exists(image_path):
        #    os.remove(image_path)
        #if os.path.exists(img_local_path):
        #    os.remove(img_local_path)
        os.rename(image_path,img_local_path)
        return jsonify({"error": 1001, "message": u"识别失败", "detected": False, "recognized": False})

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
                if not os.path.exists(img_path):
                    img_path = save_embedding.download_img_for_svm(info['url'], info['group_id'], info['face_id'], style=info['style'])
                if img_path:
                    if not os.path.exists(embedding_path):
                        img = misc.imread(os.path.expanduser(img_path))  # 手动裁剪后的图片需要再缩放一下
                        aligned = misc.imresize(img, (image_size, image_size))
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
                db.session.add(t)
                db.session.commit()
                #db.session.delete(t)

                #delete the train image
                filepath = t.filepath
                print('drop filepath:', filepath)
                if filepath and os.path.exists(filepath):
                    os.remove(filepath)
            for t in people_in_db:
                if rm_reason is not None and rm_reason == "notface":
                    t.classId = "notface"
                    db.session.add(t)
                    db.session.commit()
                    print("update None-face image 2")
                    continue

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
                        aligned = misc.imresize(img, (image_size, image_size))
                        misc.imsave(img_path, aligned)
                        embedding = featureCalculation(img_path)
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
                    aligned = misc.imresize(img, (image_size, image_size))
                    misc.imsave(img_path, aligned)
                    embedding = featureCalculation(img_path)
                    embedding_path = save_embedding.get_embedding_path(img_path)
                    save_embedding.create_embedding_string(embedding, embedding_path)
                    FACE_COUNT[style] += 1
                    train.filepath = img_path
                    print('{} style face count'.format((FACE_COUNT[style])))

                db.session.add(train)
                db.session.commit()

                if SAVE_FULL_BODY:
                    mobilenet_labeled_download(url, group_id, face_id)

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
                        embedding_path = save_embedding.get_embedding_path(img_path)
                        if os.path.isfile(embedding_path) is False:
                            #img = misc.imread(os.path.expanduser(img_path))  # 手动裁剪后的图片需要再缩放一下
                            #aligned = misc.imresize(img, (image_size, image_size))
                            #misc.imsave(img_path, aligned)
                            if embedding is None:
                                embedding = featureCalculation(img_path)
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

                if SAVE_FULL_BODY:
                    mobilenet_labeled_download(url, group_id, face_id)

            else:
                print("already in dataset")

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
                clean_droped_embedding(current_groupid)

                svm_current_groupid_basepath = os.path.join('faces', current_groupid)

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

                    ret_val = classifier_classify_new.train_svm_with_embedding(args_list)
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

# flask默认的启动
if __name__ == '__main__':
    args = parse_arguments(sys.argv[1:])
    if args.report is True:
        print('Upload and report to WorkAI')
        DO_NOT_UPLOAD_IMAGE = False
        DO_NOT_REPORT_TO_SERVER = False
    port = args.port
    host = args.host
    gFlask_port = port

    if port == 5000:
        try:
            basepath = os.path.abspath(os.getenv('RUNTIME_BASEDIR',os.path.dirname(__file__)))
            start_filepath = '/start'
            dotstart_filepath = '/.start'
            checkupdate_filepath = '/data/checkupdate'
            git_start_filepath = os.path.join(basepath, 'start')
            if os.path.exists(git_start_filepath):
                cmd = "cp -f {} {}".format(git_start_filepath, start_filepath)
                out_put = subprocess.call(cmd, shell=True)
                print("{}, exec result is {}".format(cmd, out_put))
                cmd = "chmod 755 {}".format(start_filepath)
                out_put = subprocess.call(cmd+";exit 0", shell=True)
                print("{}, exec result is {}".format(cmd, out_put))
            else:
                print("{} not exist!".format(git_start_filepath))

            git_dotstart_filepath = os.path.join(basepath, '.start')
            if os.path.exists(git_dotstart_filepath):
                cmd = "cp -f {} {}".format(git_dotstart_filepath, dotstart_filepath)
                out_put = subprocess.call(cmd, shell=True)
                print("{}, exec result is {}".format(cmd, out_put))
                cmd = "chmod 755 {}".format(dotstart_filepath)
                out_put = subprocess.call(cmd+";exit 0", shell=True)
                print("{}, exec result is {}".format(cmd, out_put))
            else:
                print("{} not exist!".format(git_dotstart_filepath))

            git_checkupdate_filepath = os.path.join(basepath, 'checkupdate')
            if os.path.exists(git_checkupdate_filepath):
                cmd = "cp -f {} {}".format(git_checkupdate_filepath, checkupdate_filepath)
                out_put = subprocess.call(cmd, shell=True)
                print("{}, exec result is {}".format(cmd, out_put))
                cmd = "chmod 755 {}".format(checkupdate_filepath)
                out_put = subprocess.call(cmd+";exit 0", shell=True)
                print("{}, exec result is {}".format(cmd, out_put))
            else:
                print("{} not exist!".format(git_checkupdate_filepath))

            cmd = "ps -aux|grep .start | grep 5001 | awk '{print $2}' | xargs kill -9"
            out_put = subprocess.call(cmd, shell=True)
            print("{}, exec result is {}".format(cmd, out_put))
            cmd = "ps -aux|grep python | grep 5001 | awk '{print $2}' | xargs kill -9"
            out_put = subprocess.call(cmd, shell=True)
            print("{}, exec result is {}".format(cmd, out_put))
            cmd = "chmod a+x {}".format(start_filepath)
            out_put = subprocess.call(cmd+";exit 0", shell=True)
            print("{}, exec result is {}".format(cmd, out_put))
        except OSError as e:
            print("Update shell script execpt:{}".format(e))

    print("port = {}".format(port))
    if port == 5001:
        exit()

    uploadImg = uploadFileInit(updatePeopleImgURL)
    #only master process need mqtt
    if port == 5000:
        #TODO: UUID when no eth0/wlan0
        mqttc = MyMQTTClass(getUUID() + str(port))
        mqttc.initialize(updata_trainset, disposeAutoGroupFunc)
        mqttc.registerUpateTrainsetHandle(updateDataSet)
        mqttc.registerMQTTDebugOnOffHandle(mqttDebugOnOff)
        mqttc.registerDropPersonHandle(dropPersonFunc)
        mqttc.registerMQTTFinalSyncDatasetsHandle(disposeFinalSyncDatasetsThreadFunc)
        mqttc.registerMQTTSyncStatusInfoHandle(disposeSyncStatusInfoThreadFunc)

    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    # if not os.path.exists(os.path.join(BASEDIR, 'data.sqlite')):
    #     db.create_all()
    if not os.path.exists(os.path.join(BASEDIR, 'data.sqlite')):
        if os.path.exists(os.path.join(BASEDIR, 'data_init')):
            shutil.copyfile(os.path.join(BASEDIR, 'data_init'), os.path.join(BASEDIR, 'data.sqlite'))

    if not os.path.exists(TMP_DIR_PATH):
        os.makedirs(TMP_DIR_PATH)

    if SVM_CLASSIFIER_ENABLED:
        svm_face_dataset = os.path.join(BASEDIR, 'face_dataset')
        svm_face_embedding = os.path.join(BASEDIR, 'face_embedding')
        svm_tmp_dir = os.path.join(BASEDIR, 'faces', 'noname', 'person')
        svm_face_testdataset = os.path.join(BASEDIR, 'face_testdataset')
        svm_stranger_testdataset = os.path.join(BASEDIR, 'stranger_testdataset')
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


    # do nothing, just warm up
    featureCalculation('./image/Mike_Alden_0001.png')
    if port == 5000:
        #thread.start_new_thread(mqttc.run,('',))
        mqttc.start()
    # threading.Thread(target=mqttc.run, args=('',)).start()
        migration()

    if EN_OBJECT_DETECTION == True:
        gbottlenecks = GenerateBottlenecks()
        trainfromfottlenecks = TrainFromBottlenecks()
    if SAVE_FULL_BODY:
        mobilenet = MobilenetBottlenecks()

    # Timer thread start
    #timer = Timer()
    #timer.restart()
    #threading.Thread(target=post_gif_loop, name='LoopThread').start()

    app.run(host=host,port=port)
    # manager.run()  # run: $ python upload_api.py runserver


def crons_start():
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    if not os.path.exists(os.path.join(BASEDIR, 'data.sqlite')):
        db.create_all()
