# coding=utf-8
from __future__ import division
import cv2
import math
#import sched
import time
import os
import sys
import shutil
import numpy as np
import threading
from threading import Timer
from scipy import misc
from collections import Counter
from collections import OrderedDict

from migrate_db import db, TrackImageSet
from sqlalchemy import desc
from sqlalchemy import text
from utilslib.save2gst import save2gst, save2gst_autolabel
#from upload_api import upload_forecast_result
from utilslib.getDeviceInfo import deviceId, get_current_groupid
'''
from sqlalchemy import JSON
from sqlalchemy import cast
records = db_session.query(Resource).filter(Resources.data["lastname"] == cast("Doe", JSON)).all()

from sqlalchemy.types import Integer
data = Target.query.order_by(Target.product['salesrank'].cast(Integer))
'''


'''
'''

BASEPATH = os.path.abspath(os.path.dirname(__file__))
track_image_path = os.path.join(BASEPATH, 'tracker')
version_arr = (cv2.__version__).split('.')
major_ver = version_arr[0]
minor_ver = version_arr[1]
subminor_ver = version_arr[2]
update_timer = None
update_count = 0
#schedule = sched.scheduler(time.time, time.sleep)
OBJECT_TRACK_DB =  os.path.join(BASEPATH, 'object_track_db.json')
g_timer = None
g_time_period = 1000
g_object_track_callback = None
g_forceTriggerArray = []
g_first_run = True
g_is_loop_started = False

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

    def find(self, key):
        return self.collection.get(key)

    def insert(self, key, fields):
        self.collection[key] = fields
        if self.isSave is True:
            self.save()

    def update(self, key, fields):
        #self.debug("Before update")
        if key in self.collection:
            self.collection.update({key:fields})
            #self.debug("After update")
            if self.isSave is True:
                self.save()

    def upsert(self, key, fields):
        #self.debug("Before upsert")
        if key in self.collection:
            self.update(key, fields)
        else:
            self.insert(key, fields)
        #self.debug("After upsert")

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

    def debug(self, prefix):
        for key in self.collection:
            print("{}: {}: {}".format(prefix, key, self.collection[key]))


def loopFunction(enter_time, interval, isloop):
    global object_track_db
    global g_forceTriggerArray
    global g_first_run

    #print("loopFunction: in, isloop={}".format(isloop))
    handle_queue_dic = object_track_db.fetch()
    for key in handle_queue_dic:
        print("List handle_queue_dic[{}]={}".format(key, handle_queue_dic[key]))
        if g_first_run is False and isloop:
            handle_queue_dic[key] = int(handle_queue_dic[key]) - 1
            object_track_db.update(key, handle_queue_dic[key])
            if key in g_forceTriggerArray or handle_queue_dic[key] <= 0:
                print("  0, track_id={}".format(key))
                update_facial_recognition_result3(key)
                print("  0-1, track_id={}".format(key))
                object_track_db.remove(key)
                if key in g_forceTriggerArray:
                    g_forceTriggerArray.remove(key)
                print("  1, Remove key {} from handle_queue_dic".format(key))
        else:
            print("  2, track_id={}".format(key))
            object_track_db.update(key, 0)
    handle_queue_dic = object_track_db.fetch()
    if not handle_queue_dic:
        TrackImageSet.query.delete()
        db.session.commit()
    #schedule.enter(1, 0, loopFunction, (interval,True,))
    g_first_run = False
    if isloop:
        if len(g_forceTriggerArray) > 0:
            del g_forceTriggerArray
            g_forceTriggerArray = []
        #print("g_forceTriggerArray={}".format(g_forceTriggerArray))
        #print("loopFunction, timer start again.")
        Timer(1, loopFunction, (time.time(),1,True,)).start()

object_track_db = MyDB(OBJECT_TRACK_DB)
def start_loopFunction():
    global g_is_loop_started;
    if g_is_loop_started is False:
        g_is_loop_started = True
        Timer(1, loopFunction, (time.time(),3,True,)).start()

#schedule.enter(1, 0, loopFunction, (1,True,))
#schedule.run()
#Timer(1, loopFunction, (time.time(),1,True,)).start()


def compare2(emb1, emb2):
    dist = np.sum([emb2]*emb1, axis=1)
    return dist


def check_faces_in_two_images_1(image1, image2, bbox):
    tracker_types = ['BOOSTING', 'MIL','KCF', 'TLD', 'MEDIANFLOW', 'GOTURN']
    tracker_type = tracker_types[2]
    print("minor_ver={}".format(minor_ver))
    if int(minor_ver) < 3:
        tracker = cv2.Tracker_create(tracker_type)
    else:
        if tracker_type == 'BOOSTING':
            tracker = cv2.TrackerBoosting_create()
        if tracker_type == 'MIL':
            tracker = cv2.TrackerMIL_create()
        if tracker_type == 'KCF':
            tracker = cv2.TrackerKCF_create()
        if tracker_type == 'TLD':
            tracker = cv2.TrackerTLD_create()
        if tracker_type == 'MEDIANFLOW':
            tracker = cv2.TrackerMedianFlow_create()
        if tracker_type == 'GOTURN':
            tracker = cv2.TrackerGOTURN_create()
    previous_bbox = bbox
    ok = tracker.init(image1, bbox)
    ok, bbox = tracker.update(image2)
    if ok:
        debug_save_image("track_image1", image1, "", None)
        debug_save_image("track_image2", image2, "", None)
        debug_save_image("rect_image1", image1, "", previous_bbox)
        debug_save_image("rect_image2", image2, "", bbox)
        return True, bbox
    else:
        return False, None

def check_faces_in_two_images(image1, image2, bbox):
    similarity = 0.7
    top_left = None
    confidence = None

    methods = ['cv2.TM_CCOEFF', 'cv2.TM_CCOEFF_NORMED', 'cv2.TM_CCORR',
            'cv2.TM_CCORR_NORMED', 'cv2.TM_SQDIFF', 'cv2.TM_SQDIFF_NORMED']

    meth = 'cv2.TM_SQDIFF_NORMED'
    method = eval(meth)
    # Apply template Matching
    template = image1[bbox[1]:(bbox[1]+bbox[3]), bbox[0]:(bbox[0]+bbox[2])]
    #w, h = template.shape[::-1]
    image_size = np.asarray(template.shape)[0:2]
    w = image_size[1]
    h = image_size[0]
    res = cv2.matchTemplate(image2, template, method)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
    # If the method is TM_SQDIFF or TM_SQDIFF_NORMED, take minimum
    if method in [cv2.TM_SQDIFF, cv2.TM_SQDIFF_NORMED]:
        confidence = min_val
        if min_val <= 1-similarity:
            top_left = min_loc
    else:
        confidence = max_val
        if max_val >= similarity:
            top_left = max_loc
    if top_left == None:
        print("Track Failed. confidence={}".format(confidence))
        return False, None
    else:
        previous_bbox = bbox
        bbox = (top_left[0], top_left[1], w, h)
        debug_save_image("track_image1", image1, "", None)
        debug_save_image("track_image2", image2, "", None)
        debug_save_image("rect_image1", image1, "", previous_bbox)
        debug_save_image("rect_image2", image2, "", bbox)

        bottom_right = (top_left[0] + w, top_left[1] + h)
        print("top_left={}, bottom_right={}".format(top_left, bottom_right))
        print("Track Suc. confidence={}".format(confidence))
        return True, bbox


'''
+++++++++++++++++++++++++++++
+
+           1/8
+     |--------------|
+     |              |
+     |              |
+     |      1       |
+     |              |
+     |              |
+     |______________|
+
+
+          11/8
+
+++++++++++++++++++++++++++++
'''
def compute_object_rect(rect, image_width, image_height):
    target_image_width = target_image_height = 160
    left = rect[0]  # - target_image_width/8.0
    top = rect[1] - target_image_width/4.0
    width = rect[2]*1.25
    height = rect[3]*2.5
    if left < 0:
        width = width+left
        left = 0
    if top < 0:
        height = height+top
        top = 0
    if left + width > image_width:
        width = image_width - left
    if top + height > image_height:
        height = image_height - top
    print("Compute object rect={} -->({}, {}, {}, {})".format(rect, int(left), int(top), int(width), int(height)))
    return (int(left), int(top), int(width), int(height))


def computeOverlapArea(rect1, rect2):
    overlap_area = 0

    x1 = rect1[0]
    y1 = rect1[1]
    width1 = rect1[2]
    height1 = rect1[3]
      
    x2 = rect2[0]
    y2 = rect2[1]
    width2 = rect2[2]
    height2 = rect2[3]
      
    endx = max(x1+width1,x2+width2)
    startx = min(x1,x2)
    width = width1+width2-(endx-startx)

    endy = max(y1+height1,y2+height2)
    starty = min(y1,y2)
    height = height1+height2-(endy-starty)
      
    if width<=0 or height<=0:
        overlap_area = 0
    else:
        Area = width*height
        Area1 = width1*height1
        Area2 = width2*height2
        overlap_area = int(Area)
        '''
        ratio = Area/(Area1+Area2-Area)
        if ratio>=0.5:
            D = 1
        else:
            D = 0
        '''
    return overlap_area

def compare_object_rect(rectArray, compare_rect):
    overlap_array = []
    for rect in rectArray:
        print("Compare: rect={}, compare_rect={}".format(rect, compare_rect))
        overlap_area = computeOverlapArea(rect, compare_rect)
        print("overlap_area = {}".format(overlap_area))
        overlap_array.append(overlap_area)
    max_overlap = 0
    index = -1
    for i in range(len(overlap_array)):
        if overlap_array[i] > max_overlap:
            max_overlap = overlap_array[i]
            index = i
    return index

def update_facial_recognition_result(objects):
    nrof_faces = len(objects)
    if nrof_faces > 0:
        counter = Counter()
        for i in range(nrof_faces):
            counter[objects[i]["class_name"]] += 1
        top5_class_name = counter.most_common(5)
        print("top5_class_name={}".format(top5_class_name))
        if len(top5_class_name) > 0:
            top_class_name = top5_class_name[0][0]
            top_count = top5_class_name[0][1]
            if len(top5_class_name) > 1:
                second_class_name = top5_class_name[1][0]
                second_count = top5_class_name[1][1]
                if top_count == second_count:
                    max_top_score = 0
                    max_second_score = 0
                    for i in range(nrof_faces):
                        if objects[i]["class_name"] == top_class_name and objects[i]["score"] > max_top_score:
                            max_top_score = objects[i].score
                        elif objects[i]["class_name"] == second_class_name and objects[i]["score"] > max_second_score:
                            max_second_score = objects[i]["score"]
                    if max_top_score < max_second_score:
                        print("One person two faces, use the face with higher score: {}/{}".format(second_class_name, top_class_name))
                        top_class_name = second_class_name
            for i in range(nrof_faces):
                if "class_name" in objects[i] and objects[i]["class_name"] != top_class_name:
                    if "correct_name" not in objects[i] or objects[i]["correct_name"] != top_class_name:
                        objects[i]["correct_name"] = top_class_name
                        print(">>>>  Correct one recognition: {} --> {}, {}".format(objects[i]["class_name"], objects[i]["correct_name"], objects[i]["image_path"]))
            for i in range(nrof_faces):
                if "correct_name" in objects[i] and objects[i]["correct_name"]:
                    print("Correct recognition results: {}: {} --> {}".format(i, objects[i]["class_name"], objects[i]["correct_name"]))
                else:
                    print("Correct recognition results: {}: {} --> None".format(i, objects[i]["class_name"]))
        else:
            print("Error: no top5_class_name!!")
        return objects
    else:
        return objects

def debug_save_image(type, image, image_path, bb):
    image_size = np.asarray(image.shape)[0:2]
    image_width = image_size[1]
    image_height = image_size[0]
    if bb:
        print("debug_save_image: {}/{}, ({},{},{},{})".format(image_width, image_height, bb[1], (bb[1]+bb[3]), bb[0], (bb[0]+bb[2])))
        cropped = image[bb[1]:(bb[1]+bb[3]), bb[0]:(bb[0]+bb[2])]
    else:
        cropped = image
    cropped_image_path = os.path.join(track_image_path, "{}_{}.png".format(int(time.time()*1000), type))
    print("cropped_image_path={}".format(cropped_image_path))
    misc.imsave(cropped_image_path, cropped)


def update_facial_recognition_result2(track_id):
    persons = []
    err_predicts_labels = []
    err_predicts_persons = []
    max_facecnt = 0
    person_id = None
    track_images_array = TrackImageSet.query.filter(TrackImageSet.track_id==track_id).all() #.order_by(desc(TrackImageSet.ts))
    #print("track_images_array={}".format(track_images_array))
    if track_images_array:
        for track_image in track_images_array:
            #print(">> track_image={}".format(track_image.__dict__))
            nrof_faces = len(track_image.faces_array)
            for i in range(nrof_faces):
                persons.append(track_image.faces_array[i])
            if track_image.facecnt > max_facecnt:
                max_facecnt = track_image.facecnt

        if len(persons) > 0:
            #print("persons={}".format(persons))
            counter = Counter()
            for i in range(len(persons)):
                if persons[i]["face_accuracy"] > 0:
                    counter[persons[i]["class_name"]] += 1
            top_class_name = counter.most_common(10)
            print("top_class_name={}".format(top_class_name))

            if len(top_class_name) > 0:
                #Exchange the class name of the same count
                '''
                for i in range(len(top_class_name)):
                    if i == 0:
                        continue
                    if top_class_name[i][1] == top_class_name[i-1][1]:
                        first_class_name = top_class_name[i-1][0]
                        second_class_name = top_class_name[i][0]
                        first_score = 0.0
                        second_score = 0.0
                        for j in range(len(persons)):
                            if persons[j]["class_name"] == first_class_name:
                                if float(persons[j]["score"]) > first_score:
                                    first_score = float(persons[j]["score"])
                            elif persons[j]["class_name"] == second_class_name:
                                if float(persons[j]["score"]) > second_score:
                                    second_score = float(persons[j]["score"])
                        if first_score < second_class_name:
                            temp_class_name = top_class_name[i-1][0]
                            top_class_name[i-1] = list(top_class_name[i-1])
                            top_class_name[i-1][0] = top_class_name[i][0]
                            top_class_name[i-1] = tuple(top_class_name[i-1])
                            top_class_name[i] = list(top_class_name[i])
                            top_class_name[i][0] = temp_class_name
                            top_class_name[i] = tuple(top_class_name[i])
                '''
                for i in range(len(top_class_name)):
                    for j in range(i+1,len(top_class_name)):
                        if top_class_name[i][1] == top_class_name[j][1]:
                            first_class_name = top_class_name[i][0]
                            second_class_name = top_class_name[j][0]
                            first_score = 0.0
                            second_score = 0.0
                            for m in range(len(persons)):
                                if persons[m]["class_name"] == first_class_name:
                                    if float(persons[m]["score"]) > first_score:
                                        first_score = float(persons[m]["score"])
                                elif persons[m]["class_name"] == second_class_name:
                                    if float(persons[m]["score"]) > second_score:
                                        second_score = float(persons[m]["score"])
                            if first_score < second_score:
                                temp_class_name = top_class_name[j][0]
                                top_class_name[j] = list(top_class_name[j])
                                top_class_name[j][0] = top_class_name[i][0]
                                top_class_name[j] = tuple(top_class_name[j])
                                top_class_name[i] = list(top_class_name[i])
                                top_class_name[i][0] = temp_class_name
                                top_class_name[i] = tuple(top_class_name[i])

                #Find the err predict labels
                person_id = top_class_name[0][0]
                for i in range(len(top_class_name)):
                    print("max_facecnt={}, top_class_name[{}][0]={}, top_class_name[{}][1]={}".format(max_facecnt, i, top_class_name[i][0], i, top_class_name[i][1]))
                    if i < max_facecnt:
                        continue
                    if top_class_name[i][1] <= 3:
                        err_predicts_labels.append(top_class_name[i][0])
                print("err_predicts_labels = {}".format(err_predicts_labels))
                #Find the err predict persons
                #if len(err_predicts_labels) > 0:
                for track_image in track_images_array:
                    nrof_faces = len(track_image.faces_array)
                    #print(">> track_image={}".format(track_image.__dict__))
                    #print(">> id={}, track_id={}, image_path={}".format(track_image.id, track_image.track_id, track_image.image_path))
                    for i in range(nrof_faces):
                        if track_image.faces_array[i]["class_name"] in err_predicts_labels:
                            err_predicts_persons.append(track_image.faces_array[i])
                        else:
                            key = track_image.faces_array[i]["key"]
                            print("1, key={}, {}".format(key, track_image.faces_array[i]))
                            if "isNotify" not in track_image.faces_array[i] or track_image.faces_array[i]["isNotify"] == 0:
                                print("2, key={}".format(key))
                                track_image.faces_array[i]["isNotify"] = 1
                                #if g_object_track_callback:
                                #    g_object_track_callback(key, track_image.faces_array[i])
                                TrackImageSet.query.filter_by(id=track_image.id).update(dict(faces_array=track_image.faces_array))
                                db.session.commit()
                print("err_predicts_persons={}".format(err_predicts_persons))
                #Send the error predict persons to server side
                for forecast_result in err_predicts_persons:
                    print("forecast_result={}".format(forecast_result))
                    uuid = forecast_result["uuid"]
                    objid = forecast_result["face_id"]
                    url = forecast_result["url"]
                    face_accuracy = forecast_result["face_accuracy"]
                    fuzziness = forecast_result["face_fuzziness"]
                    people_sqlId = forecast_result["people_sqlId"]
                    style = forecast_result["img_style_str"]
                    img_ts = forecast_result["ts"]
                    tid = forecast_result["trackerId"]
                    p_ids = forecast_result['p_ids']
                    save2gst(uuid, objid, url, '', 'face', face_accuracy, int(fuzziness), int(people_sqlId), style, img_ts, tid, p_ids, 'remove')  # 发送请求给workai
                print("max_facecnt={}".format(max_facecnt))
                if max_facecnt == 1:
                    print("Group known people, person_id={}, {}".format(person_id, len(persons)))
                    save2gst_stranger(person_id, persons)
                elif max_facecnt > 1:
                    save2gst_multiplePeople(person_id, persons)
            else:  #Stranger
                print("Group unknown people={}".format(len(persons)))
                #g_object_track_callback("stranger", persons)
                save2gst_stranger('', persons)

def update_facial_recognition_result3(track_id):
    persons = []
    err_predicts_labels = []
    err_predicts_persons = []
    max_facecnt = 0
    person_id = None
    track_images_array = TrackImageSet.query.filter(TrackImageSet.track_id==track_id).all() #.order_by(desc(TrackImageSet.ts))
    print("track_images_array={}".format(track_images_array))
    if track_images_array:
        for track_image in track_images_array:
            #print(">> track_image={}".format(track_image.__dict__))
            nrof_faces = len(track_image.faces_array)
            for i in range(nrof_faces):
                persons.append(track_image.faces_array[i])
            if track_image.facecnt > max_facecnt:
                max_facecnt = track_image.facecnt

        if len(persons) > 0:
            #print("persons={}".format(persons))
            counter = Counter()
            for i in range(len(persons)):
                if persons[i]["face_accuracy"] > 0:
                    counter[persons[i]["class_name"]] += 1
            top_class_name = counter.most_common(10)
            print("top_class_name={}".format(top_class_name))

            if len(top_class_name) > 0:
                for i in range(len(top_class_name)):
                    for j in range(i+1,len(top_class_name)):
                        if top_class_name[i][1] == top_class_name[j][1]:
                            first_class_name = top_class_name[i][0]
                            second_class_name = top_class_name[j][0]
                            first_score = 0.0
                            second_score = 0.0
                            for m in range(len(persons)):
                                if persons[m]["class_name"] == first_class_name:
                                    if float(persons[m]["score"]) > first_score:
                                        first_score = float(persons[m]["score"])
                                elif persons[m]["class_name"] == second_class_name:
                                    if float(persons[m]["score"]) > second_score:
                                        second_score = float(persons[m]["score"])
                            if first_score < second_score:
                                temp_class_name = top_class_name[j][0]
                                top_class_name[j] = list(top_class_name[j])
                                top_class_name[j][0] = top_class_name[i][0]
                                top_class_name[j] = tuple(top_class_name[j])
                                top_class_name[i] = list(top_class_name[i])
                                top_class_name[i][0] = temp_class_name
                                top_class_name[i] = tuple(top_class_name[i])

                #Find the err predict labels
                person_id = top_class_name[0][0]
                for i in range(len(top_class_name)):
                    print("max_facecnt={}, top_class_name[{}][0]={}, top_class_name[{}][1]={}".format(max_facecnt, i, top_class_name[i][0], i, top_class_name[i][1]))
                    if i < max_facecnt:
                        continue
                    if top_class_name[i][1] <= 3:
                        err_predicts_labels.append(top_class_name[i][0])
                print("err_predicts_labels = {}".format(err_predicts_labels))
                #Find the err predict persons
                #if len(err_predicts_labels) > 0:
                recognized_persons = []
                for track_image in track_images_array:
                    nrof_faces = len(track_image.faces_array)
                    #print(">> track_image={}".format(track_image.__dict__))
                    #print(">> id={}, track_id={}, image_path={}".format(track_image.id, track_image.track_id, track_image.image_path))
                    for i in range(nrof_faces):
                        if track_image.faces_array[i]["class_name"] in err_predicts_labels:
                            err_predicts_persons.append(track_image.faces_array[i])
                        else:
                            if track_image.faces_array[i]["face_accuracy"] > 0:
                                recognized_persons.append(track_image.faces_array[i])
                            key = track_image.faces_array[i]["key"]
                            print("1, key={}, {}".format(key, track_image.faces_array[i]))
                            if "isNotify" not in track_image.faces_array[i] or track_image.faces_array[i]["isNotify"] == 0:
                                print("2, key={}".format(key))
                                track_image.faces_array[i]["isNotify"] = 1
                                #if g_object_track_callback:
                                #    g_object_track_callback(key, track_image.faces_array[i])
                                TrackImageSet.query.filter_by(id=track_image.id).update(dict(faces_array=track_image.faces_array))
                                db.session.commit()
                print("err_predicts_persons={}".format(err_predicts_persons))
                #Send the error predict persons to server side
                for forecast_result in err_predicts_persons:
                    print("forecast_result={}".format(forecast_result))
                    uuid = forecast_result["uuid"]
                    objid = forecast_result["face_id"]
                    url = forecast_result["url"]
                    face_accuracy = forecast_result["face_accuracy"]
                    fuzziness = forecast_result["face_fuzziness"]
                    people_sqlId = forecast_result["people_sqlId"]
                    style = forecast_result["img_style_str"]
                    img_ts = forecast_result["ts"]
                    tid = forecast_result["trackerId"]
                    p_ids = forecast_result['p_ids']
                    #save2gst(uuid, objid, url, '', 'face', face_accuracy, int(fuzziness), int(people_sqlId), style, img_ts, tid, p_ids, 'remove')  # 发送请求给workai
                print("max_facecnt={}".format(max_facecnt))
                if max_facecnt == 1:
                    print("Autolabel: Group known people, person_id={}, len(persons)={}, len(recognized_persons)={}".format(person_id, len(persons), len(recognized_persons)))
                    if len(recognized_persons) > 2:
                        folder_path = get_person_train_dataset_path(person_id)
                        print("Autolabel, folder_path={}".format(folder_path))
                        if folder_path is not None and os.path.exists(folder_path) and os.path.isdir(folder_path):
                            num_files = 0
                            for filename in os.listdir(folder_path):
                                extension = filename.rsplit('.', 1)[1]
                                if extension is not None and extension.lower() == 'png':
                                    num_files += 1
                            print("Autolabel: num_files={}".format(num_files))
                            if num_files > 30:
                                print("Train data size is more than 10, no need to add more. {}".format(os.listdir(folder_path)));
                                return
                        return_persons = check_if_can_autolabel(recognized_persons)
                        if len(return_persons) > 0:
                            print("Autolabel: len(recognized_persons)={}, len(return_persons) ={}".format(len(recognized_persons), len(return_persons)))
                            save2gst_autolabel(person_id, return_persons)
                        else:
                            print("Autolabel: NOT, recognized_persons={}, return_persons={}".format(recognized_persons, return_persons))
                #elif max_facecnt > 1:
                #    save2gst_multiplePeople(person_id, persons)
            else:  #Stranger
                print("Group unknown people={}".format(len(persons)))
                #g_object_track_callback("stranger", persons)
                #save2gst_stranger('', persons)

def get_person_train_dataset_path(face_id, style='front'):
    group_id = get_current_groupid();
    group_path = os.path.join(BASEPATH, 'data', 'faces', group_id)
    train_dataset = os.path.join(group_path, style, 'face_dataset')
    if not os.path.exists(train_dataset):
        return None

    foldername = '{}_{}'.format(group_id, face_id)
    folder_path = os.path.join(train_dataset, foldername)
    if not os.path.exists(folder_path):
        return None
    return folder_path

cascPath = 'haarcascade_frontalface_default.xml'
#cv2.ocl.setUseOpenCL(True)
#print(cv2.ocl.haveOpenCL())
faceCascade = cv2.CascadeClassifier(cascPath)
def check_if_can_autolabel(persons):
    autolabel_persons = []
    highscore_person = None
    for m in range(len(persons)):
        person = persons[m]
        uuid = person["uuid"]
        objid = person["face_id"]
        url = person["url"]
        accuracy = person["face_accuracy"]
        if accuracy < 0.5:
            continue
        fuzziness = person["face_fuzziness"]
        sqlId = person["people_sqlId"]
        style = person["img_style_str"]
        img_ts = person["ts"]
        tid = person["trackerId"]
        p_ids = person["p_ids"]
        align_image_path = person["align_image_path"]
        position = ''
        img_type = 'face'
        isBadQuality = False

        if fuzziness < 200:
            continue
        if style is not None:
            styles = style.split('|')
            for style in styles:
                if style == 'dirty' or style == 'lower_head' or style == 'blury':
                    print("check_if_can_autolabel: dirty or low_pixel or blurry pictures, discard it: url={}, style={}".format(url, style))
                    isBadQuality = True
                    break
                if style == 'left_side' or style == 'right_side':
                    isBadQuality = True
                    accuracy = 0
                    print("save2gst_stranger: left_side or right_side pictures, set accuracy to false: url={}, style={}".format(url, style))
                    break
            if isBadQuality is True:
                continue
        else:
            print("check_if_can_autolabel: style is None, what's wrong? url={}".format(url))

        img = misc.imread(os.path.expanduser(align_image_path))
        img_grey = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY,1)
        faces = faceCascade.detectMultiScale(
            img_grey,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(30, 30),
            flags=cv2.CASCADE_SCALE_IMAGE   #cv2.cv.CV_HAAR_SCALE_IMAGE #CV_HAAR_DO_ROUGH_SEARCH
        )
        if faces is not None and len(faces) > 0:
            print("check_if_can_autolabel: HAR detected face: len(faces)={}".format(len(faces)));
            if highscore_person is None or accuracy > highscore_person["face_accuracy"]:
                highscore_person = person
    if highscore_person is not None:
        autolabel_persons.append(person)
    return autolabel_persons


def process_start_timer():
    global g_timer
    process_cancel_timer()
    g_timer = Timer(3, loopFunction, (time.time(),1,False,))
    g_timer.start()
    print("Object track start timer...")

def process_cancel_timer():
    global g_timer
    start_loopFunction()
    if g_timer:
        g_timer.cancel()
        g_timer = None
        print("Object track cancel timer!")

def process_object_track(image_path, ts, faces_array, callback=None):
    global update_count
    global update_timer
    global g_object_track_callback
    global g_forceTriggerArray

    g_object_track_callback = callback
    #handle_queue_dic = object_track_db.fetch()
    #for key in handle_queue_dic:
    #    if key >= ts:
    #        object_track_db.update(key, 30)
    #        print("key{} > ts{}, update to 30".format(key, ts))

    print("process_object_track in...")
    start_time = time.time()
    nrof_faces = len(faces_array)
    if nrof_faces < 1:
        print("Error: object_track: no face!")
        return
    if not os.path.exists(image_path):
        print("Error: object_track: image_path() is missing!!".format(image_path))
        return

    #Save image to private path
    if not os.path.exists(track_image_path):
        os.mkdir(track_image_path)
    #new_path = os.path.join(track_image_path, os.path.basename(image_path))
    ##filename = img_url.rsplit('/', 1)[-1] + '.png'
    #$shutil.copy(image_path, new_path)
    #$print("process_object_track: {} --> {}".format(image_path, new_path))
    #$image_path = new_path

    track_id = None
    need_update = False
    same_image = TrackImageSet.query.filter_by(ts=ts, image_path=image_path).first()
    if same_image:
        need_update = True
        track_id = same_image.track_id
        tmp_faces_array = []
        for face_dict in same_image.faces_array:
            tmp_faces_array.append(face_dict)
        for face_dict in faces_array:
            tmp_faces_array.append(face_dict)
        print("TrackImageSet: update, tmp_faces_array={}".format(tmp_faces_array))
        TrackImageSet.query.filter_by(id=same_image.id).update(dict(faces_array=tmp_faces_array))
        object_track_db.upsert(track_id, 30)
    else:
        #last_image = TrackImageSet.query.filter(text("ts<{}".format(ts))).order_by(desc(TrackImageSet.ts)).first()
        #last_image = TrackImageSet.query.filter(text("ts<{} and ts>{}".format(str(int(ts)+1500), str(int(ts)-1500)))).order_by(desc(TrackImageSet.ts)).first()
        last_image = TrackImageSet.query.filter(text("ts<{} and ts>{}".format(str(int(ts)+int(g_time_period)), str(int(ts)-int(g_time_period))))).all()
        #if last_image:
            #if not last_image.image_path or not os.path.exists(last_image.image_path):
            #    print("Error: object_track: last_image({}) is missing!!".format(last_image))
            #    last_image = None
            #else:
            #nrof_rects = len(last_image.faces_array)
            #if nrof_rects < 1:
            #    print("Error: object_track: no faces in last_image({})!!".format(last_image))
            #    last_image = None

        #if last_image:
        #    print("ts = {}, last_image.ts={}, interval={}".format(ts, last_image.ts, int(ts) - int(last_image.ts)))
        #if not last_image or int(ts) - int(last_image.ts) > g_time_period:
        if not last_image:
            track_id = int(ts)
        else:
            min_track_id = None
            min_ts = sys.maxint
            track_id_array = []
            for image in last_image:
                if int(image.ts) < min_ts:
                    min_ts = int(image.ts)
                    min_track_id = image.track_id
                if image.track_id not in track_id_array:
                    track_id_array.append(image.track_id)
            if min_track_id is not None:
                print("min_track_id={}".format(min_track_id))
                handle_queue_dic = object_track_db.fetch()
                for key in handle_queue_dic:
                    print("   before  -->[{}]={}".format(key, handle_queue_dic[key]))
                for id in track_id_array:
                    #print("image.ts={}, image.track_id={}, min_track_id={}".format(image.ts, image.track_id, min_track_id))
                    #if image.track_id != min_track_id:
                    #    print("Delete track_id from object_track_db: {}={}".format(image.track_id, object_track_db.find(image.track_id)))
                    print("id={}, min_track_id={}".format(id, min_track_id))
                    if id != min_track_id:
                        object_track_db.remove(id)
                        TrackImageSet.query.filter_by(track_id=id).update(dict(track_id=min_track_id))
                track_id = min_track_id
                handle_queue_dic = object_track_db.fetch()
                for key in handle_queue_dic:
                    print("    after  -->[{}]={}".format(key, handle_queue_dic[key]))
            else:
                print("ERROR: no min_track_id, what's wrong?")
                track_id = int(ts)
            #count = TrackImageSet.query.filter_by(track_id=last_image.track_id).count()
            #if count != 0 and count % 12 == 0:
            #    if track_id not in g_forceTriggerArray:
            #        g_forceTriggerArray.append(track_id)
        object_track_db.upsert(track_id, 30)
        print("TrackImageSet: insert, tmp_objects={}".format(faces_array))
        trackImageSet = TrackImageSet(track_id=track_id, facecnt=nrof_faces, ts=ts, image_path=image_path, faces_array=faces_array)

    db.session.add(trackImageSet)
    db.session.commit()
    
    print("object_track: process completed! cost: {}S".format(time.time() - start_time))
    process_start_timer()
