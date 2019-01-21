# coding=utf-8
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import os, json, time, sys
import shutil
import time
import os.path
import requests
from uuid import uuid1

import numpy as np

from utilslib.save2gst import generate_protocol_string
import classifier_classify_new as classifier
from faces import save_embedding

all_face_index = 0 #每当识别出一个人脸就+1，当2个人同时出现在图片里面并且都不认识，需要区分开来

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

EXT_IMG='png'

DO_NOT_UPLOAD_IMAGE = False
DO_NOT_REPORT_TO_SERVER = False
FOR_ARLO = True

USE_DEFAULT_DATA=True   # Enable to use "groupid_default" for SVM training

SVM_CLASSIFIER_ENABLED=True
SVM_SAVE_TEST_DATASET=True
SVM_TRAIN_WITHOUT_CATEGORY=True
SVM_HIGH_SCORE_WITH_DB_CHECK=True
svm_face_dataset=None
svm_face_embedding=None
svm_tmp_dir=None
svm_face_testdataset=None
svm_stranger_testdataset=None

data_collection=None
def init_fs():
    global svm_face_dataset
    global svm_face_embedding
    global svm_tmp_dir
    global svm_face_testdataset
    global svm_stranger_testdataset

    try:
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
    except Exception as e:
        print(e)

def updatePeopleImgURL(ownerid, url, embedding, uuid, objid, img_type, accuracy, fuzziness, sqlId, style, img_ts, tid,
                       p_ids, waiting):
    print('debug updatePeopleImgURL 1')
    if len(url) < 1 or len(uuid) < 1 or len(objid) < 1 or len(img_type) < 1:
        return

    if not DO_NOT_REPORT_TO_SERVER:
        print('save2gst')
        save2gst(uuid, objid, url, '', 'face', accuracy, int(fuzziness), int(sqlId), style, img_ts, tid, p_ids, waiting)  # 发送请求给workai

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
    #embedding_bytes = embedding_string.encode('utf-8')
    img_type = forecast_result['img_type']
    waiting = forecast_result['waiting']
    do_not_report_to_server = DO_NOT_REPORT_TO_SERVER
    uploadedimgurl = None

    return generate_protocol_string(key, face_id, align_image_path,
                                               embedding='', uuid=uuid,
                                               DO_NOT_REPORT_TO_SERVER=do_not_report_to_server,block=False,
                                               objid=face_id, img_type=img_type,
                                               accuracy=face_accuracy, fuzziness=face_fuzziness, sqlId=people_sqlId,
                                               style=img_style_str, ts=ts, tid=str(trackerId), p_ids=p_ids, waiting = waiting)

def face_recognition_on_embedding(align_image_path, embedding, totalPeople, blury, uuid,
                                   current_groupid, style, trackerId,
                                   timestamp1, ts, embedding_path):
    img_objid = trackerId
    print("img_objid = {}".format(img_objid))
    print("number of people=%d" % (totalPeople))
    if totalPeople > 1:
        trackerId = str(uuid1())

    number_people=totalPeople
    img_style_str = style
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
                     'waiting': False,
                     'p_ids': None,
                     }  # 保存发送给uploadImage的数据

    forecast_result['face_fuzziness'] = blury
    print(">>> blury=%d" %(blury))
    json_data['detected'] = True

    print("2 %.2f seconds" % (time.time() - timestamp1))
    if forecast_result['face_fuzziness'] < int(data_collection.get("blury_threhold")):
        json_data, forecast_result = get_empty_faceid(current_groupid, uuid, embedding,
                                                img_style, number_people, img_objid,
                                                forecast_result)
        print("Too blurry image, skip it img_objid={}, trackerId={}".format(img_objid, trackerId))
    elif SVM_CLASSIFIER_ENABLED is True:
        #img_style = 'front'
        # embedding = embedding.reshape((1, -1))
        forecast_result['waiting'] = False
        json_data, forecast_result = SVM_classifier(embedding,align_image_path,
            uuid,current_groupid,img_style,number_people,img_objid,json_data,forecast_result, embedding_path)

    print("3 %.2f seconds" % (time.time() - timestamp1))

    if json_data['recognized'] is True:
        if webShowFace is True:
            showRecognizedImage(forecast_result['align_image_path'], 1)

    forecast_result['trackerId'] = trackerId
    # 人脸预测结果发送
    key = str(uuid1())

    _,api_url,payload = upload_forecast_result(key, forecast_result, json_data, number_people)
    json_data['key'] = key
    json_data['face_fuzziness'] = blury

    return json_data, {'api_url':api_url,'payload':payload}
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

def SVM_classifier(embedding,align_image_path,uuid,current_groupid,img_style,number_people, img_objid,json_data, forecast_result, embedding_path):
    #Save image to src/face_dataset_classify/group/person/
    if SVM_SAVE_TEST_DATASET is True:
        group_path = os.path.join(BASEDIR,svm_face_testdataset, current_groupid)
        if not os.path.exists(group_path):
            os.mkdir(group_path)
        print('test dataset group_path=%s' % group_path)

    pkl_path = ""
    if SVM_TRAIN_WITHOUT_CATEGORY is True:
        pkl_path = '{}/data/faces/{}/{}/classifier_182.pkl'.format(BASEDIR,current_groupid, 'front')
        face_dataset_path = '{}/data/faces/{}/{}/face_dataset'.format(BASEDIR,current_groupid, 'front')
    else:
        pkl_path = '{}/data/faces/{}/{}/classifier_182.pkl'.format(BASEDIR,current_groupid, img_style)
        face_dataset_path = '{}/data/faces/{}/{}/face_dataset'.format(BASEDIR,current_groupid, img_style)
    svm_detected = False

    if os.path.exists(pkl_path):
        nrof_classes = 0
        if os.path.exists(face_dataset_path):
            classes = [path for path in os.listdir(face_dataset_path) \
                        if os.path.isdir(os.path.join(face_dataset_path, path))]
            nrof_classes = len(classes)
            print("SVM_classifier: nrof_classes={}".format(nrof_classes))
        #tmp_image_path = BASEDIR + '/data/faces/noname/person/face_tmp.'+EXT_IMG
        #shutil.copyfile(align_image_path, tmp_image_path)

        # 输入embedding的预测方法, 速度很快
        svm_stime = time.time()
        _, human_string, score, top_three_name, judge_result = classifier.classify([embedding], pkl_path, embedding_path)
        if top_three_name:
            top_three_faceid = [name.split(' ')[1] for name in top_three_name]
        else:
            top_three_faceid = None

        print('-> svm classify cost {}s'.format(time.time()-svm_stime))
        print("current value of score_1 ", float(data_collection.get("score_1")))
        print("current value of score_2 ", float(data_collection.get("score_2")))
        print("current value of fuzziness_1 ", float(data_collection.get("fuzziness_1")))
        print("current value of fuzziness_2 ", float(data_collection.get("fuzziness_2")))
        print("current value of update interval  ", float(data_collection.get("_interval")))
        if human_string is not None:
            message = ""
            message2 = ""
            face_id = human_string.split(' ')[1]
            score = round(score, 2)
            fuzziness = forecast_result['face_fuzziness']
            if USE_DEFAULT_DATA is True:
                if face_id == 'defaultfaceid':
                    score = 0.0
            if not FOR_ARLO:
                if score >= float(data_collection.get("score_1")) or (score >= float(data_collection.get("score_2")) and fuzziness >= float(data_collection.get("fuzziness_1")) and fuzziness < float(data_collection.get("fuzziness_2"))):
                    found, total = check_embedding_on_detected_person_forSVM(current_groupid=current_groupid,
                                   embedding=embedding,style=img_style,classid=face_id, nrof_classes=nrof_classes)
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
            else:
                if score > float(data_collection.get("score_2")):#0.40
                    found, total = check_embedding_on_detected_person_forSVM_ByDir(current_groupid=current_groupid,
                                   embedding=embedding,style=img_style,classid=human_string.replace(' ', '_'),nrof_classes=nrof_classes)
                    if found > 0:
                        if score > float(data_collection.get("score_1")) or judge_result != 0:#0.9
                            svm_detected = True
                            message = "<1, SVM Recognized> Face ID: %s %s/%s, 2nd %s/%s" % (face_id, score, img_style, found, total)
                        else:
                            message = "<2, SVM Recognized> Face ID: %s %s/%s, 2nd %s/%s" % (face_id, score, img_style, found, total)
                    else:
                        message = "<3, SVM Recognized Not, found=0> Face ID: %s %s/%s, 2nd %s/%s" % (face_id, score, img_style, found, total)
                else:
                    message = "<4, SVM Recognized Not, Low score> Face ID: %s %s/%s" % (face_id, score, img_style)

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
            #sendDebugLogToGroup(uuid, current_groupid, message)
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
        try:
            shutil.copyfile(align_image_path, save_testdataset_filepath)
        except IOError:
            print('cant copy file from {} to {},need check later'.format(align_image_path,save_testdataset_filepath ))
            pass
    if svm_detected is False:
        json_data, forecast_result = get_empty_faceid(current_groupid, uuid, embedding,
                                                    img_style, number_people, img_objid,
                                                    forecast_result)
        print('not in train classification or need to more train_dataset')

    return json_data, forecast_result

def check_embedding_on_detected_person_forSVM(current_groupid, embedding, style, classid, nrof_classes):
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
            face_accuracy = val
            print('face_accuracy={}'.format(face_accuracy))
            threshold = 0.70
            if nrof_classes <= 5 and nrof_classes > 0:
                threshold = 0.90
            elif nrof_classes <= 10 and nrof_classes > 0:
                threshold = 0.82
            if face_accuracy >= threshold:
                found = found+1
            if total >= 500:
                break
    return found, total

def check_embedding_on_detected_person_forSVM_ByDir(current_groupid, embedding, style, classid, nrof_classes):
    total = 0
    found = 0
    people = None
    if SVM_TRAIN_WITHOUT_CATEGORY is True:
        facedir = '{}/data/faces/{}/{}/face_dataset/{}'.format(BASEDIR,current_groupid, 'front', classid)
    else:
        facedir = '{}/data/faces/{}/{}/face_dataset/{}'.format(BASEDIR,current_groupid, style, classid)
    print("check embedding: facedir = {}".format(facedir))
    embedding_array = []
    if os.path.isdir(facedir):
        image_paths = []
        images = os.listdir(facedir)
        if len(images) < 1:
            print("Check embedding: Empty directory: facedir={}".format(facedir))
            return 0, 0
        for img in images:
            img_path = os.path.join(facedir, img)
            emb_path = save_embedding.get_embedding_path(img_path)
            emb = save_embedding.read_embedding_string(emb_path)
            emb = np.asarray(emb)
            embedding_array.append(emb)
    if len(embedding_array) > 0:
        for emb in embedding_array:
            val = compare2(embedding, emb)
            total = total+1
            face_accuracy = val
            print('face_accuracy={}'.format(face_accuracy))
            '''
            threshold = 1.0
            if nrof_classes <= 5 and nrof_classes > 0:
                threshold = 1.0
            elif nrof_classes <= 10 and nrof_classes > 0:
                threshold = 1.0
            '''
            threshold = 0.42
            if face_accuracy > threshold:
                found = found+1
            if total >= 500:
                break
    return found, total

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

def compare3(emb1, emb2):
    return np.sum(np.square(emb1-emb2))

class DataCollection(object):
    def __init__(self, update_freq=10):
        self.url = "http://localhost:5000/api/parameters"
        self.pre_time = time.time()
        self.update_freq = update_freq
        self.items = self.fetch()

    def fetch(self):
        try:
            resp = requests.get(self.url)
            assert resp.status_code == 200
            r = resp.json()
        except Exception as e:
            print(e)
            #print("status_code: %s" %resp.status_code)
            # if web server not work return default values.
            r = None
            if not FOR_ARLO:
                r = {
                    "blury_threhold": "10",
                    "fuzziness_1": "40",
                    "fuzziness_2": "200",
                    "score_1": "0.75",
                    "score_2": "0.60",
                    }
            else:
                r = {
                    "blury_threhold": "60",
                    "fuzziness_1": "40",
                    "fuzziness_2": "200",
                    "score_1": "0.90",
                    "score_2": "0.40",
                    }
        if "_interval" in r:
            _freq = int(r["_interval"])
            if self.update_freq != _freq:
                self.update_freq = _freq
        r.update({"_interval": self.update_freq})
        return r

    def reload(self):
        cur_time = time.time()
        if cur_time - self.pre_time > self.update_freq:
            self.pre_time = cur_time
            self.items = self.fetch()

    def get(self, key):
        key = key.lower()
        self.reload()
        return self.items.get(key, None)

data_collection = DataCollection()
init_fs()
