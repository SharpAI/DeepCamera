# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import cv2
import numpy as np
import os, time
import shutil
import sys
from scipy import misc

requests = None

class FaceFilterClass():
    def __init__(self):
        self.DEBUG_SENDBACK = False
        self.DEBUG_SHOW_GUI = True
        self.previous_grey_img = None
        self.cv2_major = None
        self.cv2_minor = None
        self.MOTION_DETECTION_THRESHOLD = 1000
        self.NO_MOTION_DURATION = 5 #Seconds
        self.no_motion_start_time = None
        self.no_motion_image = None
        for value in cv2.__version__.split("."):
            if self.cv2_major is None:
                self.cv2_major = value
            elif self.cv2_minor is None:
                self.cv2_minor = value
                break
        print("self.cv2_major={}, self.cv2_minor={}".format(self.cv2_major, self.cv2_minor))
        if self.DEBUG_SENDBACK == True:
            global requests
            import requests as requests
    def setThreshold(self, threshold):
        if threshold > 100:
            self.MOTION_DETECTION_THRESHOLD = threshold
            print("set threshold to {}".format(threshold))

    def showOnGUI(self, isShow):
        self.DEBUG_SHOW_GUI = True if isShow else False

    def resize_image(self, img, resized_width):
        img_size = np.asarray(img.shape)[0:2]
        width = img_size[1]
        height = img_size[0]
        if width < 1.5*resized_width:
            return None, img
        #print("img: width={}, height={}".format(width, height))
        ratio = width/resized_width
        img = misc.imresize(img, (int(height/ratio), resized_width), interp='bilinear')
        '''
        img_size = np.asarray(img.shape)[0:2]
        width = img_size[1]
        height = img_size[0]
        print("resized image: width={}, height={}".format(width, height))
        '''
        return None, img

    def resize_image_by_path(self, img_path, resized_width):
        if not os.path.isfile(img_path):
            print('img_path not exists! {}'.format(img_path))
            return 'Error', 'img_path not exists!'
        img = misc.imread(os.path.expanduser(img_path))
        if img is None:
            print('Read from img_path failed! {}'.format(img_path))
            return 'Error', 'Read from img_path failed!'
        img_size = np.asarray(img.shape)[0:2]
        width = img_size[1]
        height = img_size[0]
        #print("frame: width={}, height={}".format(width, height))
        ratio = width/resized_width
        img = misc.imresize(frame, (int(height/ratio), resized_width), interp='bilinear')
        '''
        img_size = np.asarray(img.shape)[0:2]
        width = img_size[1]
        height = img_size[0]
        print("resized image: width={}, height={}".format(width, height))
        '''
        return None, img

    def get_static_image_path(self, cameraId):
        BASEPATH = os.path.abspath(os.path.dirname(__file__))
        static_image_path = os.path.join(BASEPATH, 'static_image_{}.jpg'.format(cameraId))
        return static_image_path

    def save_static_image(self, cameraId, motion_result, image_path, min_value, max_value):
        try:
            print('motion_result={}, ({}, {}) image_path={}'.format(motion_result, min_value, max_value, image_path))
            image_length = os.stat(image_path).st_size
            if os.path.isfile(image_path) is False or image_length <= 0:
                print('Error: image_path({}) is not file or file size is zero {}, length={}'.format(image_path, image_length))
                return
            static_image_path = self.get_static_image_path(cameraId)
            if self.no_motion_start_time is None:
                self.no_motion_start_time = time.time()
                if os.path.isfile(static_image_path) is True and os.stat(static_image_path) > 0:
                    self.no_motion_image = misc.imread(image_path)
                else:
                    shutil.copyfile(image_path, static_image_path)
                if self.DEBUG_SENDBACK is True:
                    fin = open(static_image_path, 'rb')
                    files = {'file': ('test.jpg', fin, 'multipart/form-data')}
                    url = 'http://192.168.103.17:3000/uploadImageWithName'
                    r = requests.post(url, files=files)
                return
            if motion_result is True:
                self.no_motion_start_time = time.time()
            current_time = time.time()
            interval = current_time - self.no_motion_start_time
            if interval > self.NO_MOTION_DURATION:
                print('Detected static image, save it to {}'.format(static_image_path))
                self.no_motion_start_time = current_time
                shutil.copyfile(image_path, static_image_path)
                if self.DEBUG_SENDBACK is True:
                    fin = open(static_image_path, 'rb')
                    files = {'file': ('test.jpg', fin, 'multipart/form-data')}
                    url = 'http://192.168.103.17:3000/uploadImageWithName'
                    r = requests.post(url, files=files)
            else:
                print('save_static_image: not save, interval={}'.format(interval))
        except Exception as e:
            print('save_static_image: Error, ', e)


    def motion_detect(self, cameraId, img):
        try:
            diff_cnt = 0
            if img is None:
                return False, [], -1, -1
            if self.previous_grey_img is None:
                self.previous_grey_img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
                return False, [], -1, -1
            grey_img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
            frameDelta = cv2.absdiff(self.previous_grey_img, grey_img)
            self.previous_grey_img = grey_img
            #frameDelta = cv2.GaussianBlur(frameDelta,(5,5),0)
            #print("frameDelta={}".format(frameDelta))
            ret, diff = cv2.threshold(frameDelta, 12, 255, cv2.THRESH_BINARY)

            diff = cv2.dilate(diff, None, iterations=2)
            if self.cv2_major == '2':
                contours, hierarchy = cv2.findContours(diff, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            else:
                contours, hierarchy = cv2.findContours(diff, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            rects = []
            try:
                min_value = sys.maxint
            except:
                min_value = sys.maxsize

            max_value = 0
            for c in contours:
                # if the contour is too small, ignore it
                if cv2.contourArea(c) < self.MOTION_DETECTION_THRESHOLD:
                    continue
                #print("cv2.contourArea(c)={}".format(cv2.contourArea(c)))
                diff_cnt += 1
                (x, y, w, h) = cv2.boundingRect(c)
                if w*h > max_value:
                    max_value = w*h
                if w*h < min_value:
                    min_value = w*h
                rects.append((x, y, w, h))
                if self.DEBUG_SHOW_GUI is True:
                    cv2.rectangle(img, (x, y), (x+w, y+h), (0, 0, 255), 2)
            #if self.showOnGUI is True:
                #cv2.imshow('contours', img)
                #cv2.imshow('dis', diff)

            #print("diff_cnt={}".format(diff_cnt))
            if diff_cnt > 0:
                return True, rects, min_value, max_value
            else:
                return False, [], min_value, max_value
        except Exception as e:
            print('motion_detect: Error, ', e)
            return False, [], -1, -1

    def template_matching(self, cameraId, template, box, image_path):
        try:
            result = False
            rects = []
            static_image_path = self.get_static_image_path(cameraId)
            static_image_length = os.stat(static_image_path).st_size
            print("template_matching: static_image_path={}, static_image_length={}".format(static_image_path, static_image_length))
            if not os.path.isfile(static_image_path) or static_image_length <= 0:
                print('template_matching: error, static_image_length({}) is not file or file size is zero {}, length={}'.format(static_image_length, static_image_length))
                return result, rects
            if template is None:
                print('template_matching: error, template is None')
                return result, rects

            print("Frank: template_matching, {}, {}".format(template.shape, len(template.shape)))
            if len(template.shape) == 3:
                h, w, _ = template.shape
            else:
                h, w = template.shape
            print("template_matching: w={}, h={}".format(w, h))
            # All the 6 methods for comparison in a list
            #methods = ['cv.TM_CCOEFF', 'cv.TM_CCOEFF_NORMED', 'cv.TM_CCORR',
            #            'cv.TM_CCORR_NORMED', 'cv.TM_SQDIFF', 'cv.TM_SQDIFF_NORMED']
            methods = ['cv2.TM_CCOEFF_NORMED']
            img = misc.imread(os.path.expanduser(static_image_path))
            #Compute new and bigger box
            img_size = np.asarray(img.shape)[0:2]
            width = img_size[1]
            height = img_size[0]
            x1, y1, x2, y2 = box
            new_x1 = x1-10 if x1 >= 10 else 0
            new_x2 = x2+10 if x2+10<=width else width
            new_y1 = y1-10 if y1 >= 10 else 0
            new_y2 = y2+10 if y2+10<=height else height
            new_box = (new_x1, new_y1, new_x2, new_y2)
            #print('new box: {} ==> {}'.format(box, new_box))
            cropped = img[new_y1:new_y2, new_x1:new_x2, :]
            if self.DEBUG_SENDBACK is True:
                misc.imsave('cropped.jpg', cropped)
                fin = open('cropped.jpg', 'rb')
                files = {'file': ('cropped.jpg', fin, 'multipart/form-data')}
                url = 'http://192.168.103.17:3000/uploadImageWithName'
                r = requests.post(url, files=files)

                misc.imsave('template.jpg', template)
                fin = open('template.jpg', 'rb')
                files = {'file': ('template.jpg', fin, 'multipart/form-data')}
                r = requests.post(url, files=files)
            cropped2 = cropped.copy()
            for meth in methods:
                cropped = cropped2.copy()
                method = eval(meth)
                # Apply template Matching
                res = cv2.matchTemplate(cropped, template, method)
                threshold = 0.7
                '''
                loc = np.where( res >= threshold)
                for pt in zip(*loc[::-1]):
                    result = True
                    box = (pt[0], pt[1], pt[0]+w, pt[1] + h)
                    print('template_matching: match suc, box={}'.format(template_matching))
                    rects.append(box)
                    #cv2.rectangle(img_rgb, pt, (pt[0] + w, pt[1] + h), (7,249,151), 2)
                '''
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
                # If the method is TM_SQDIFF or TM_SQDIFF_NORMED, take minimum
                print('template_matching: confidence={}'.format(cv2.minMaxLoc(res)))
                if max_val < threshold:
                    continue
                result = True
                if method in [cv2.TM_SQDIFF, cv2.TM_SQDIFF_NORMED]:
                    top_left = min_loc
                else:
                    top_left = max_loc
                bottom_right = (top_left[0] + w, top_left[1] + h)
                #print('template_matching: top_left={}, bottom_right={}'.format(top_left, bottom_right))
                #cv2.rectangle(img, top_left, bottom_right, 255, 2)
                #cv2.rectangle(img, (top_left[0]+new_x1, top_left[1]+new_y1), (bottom_right[0]+new_x1, bottom_right[1]+new_y1), 255, 2)
                #x, y, w, h = top_left[0], top_left[1], bottom_right[0]-top_left[0], bottom_right[1]-top_left[1]
                x, y, w, h = top_left[0]+new_x1, top_left[1]+new_y1, bottom_right[0]+new_x1, bottom_right[1]+new_y1
                print("x={}, y={}, w={}, h={}".format(x, y, w, h))
            #return result, [(x, y, w, h)]
            if self.DEBUG_SENDBACK is True:
                img_rgb = cv2.imread(image_path)
                cv2.rectangle(img_rgb, (box[0], box[1]), (box[2], box[3]), (7,249,151), 2)
                if result is True:
                    cv2.putText(img_rgb,"Fake Face",(100,100), cv2.FONT_HERSHEY_SIMPLEX, 2,(255,255,255),2,cv2.CV_AA)
                else:
                    cv2.putText(img_rgb,"Face",(100,100), cv2.FONT_HERSHEY_SIMPLEX, 2,(255,255,255),2,cv2.CV_AA)
                cv2.imwrite('camera.jpg', img_rgb)
                fin = open('camera.jpg', 'rb')
                files = {'file': ('camera.jpg', fin, 'multipart/form-data')}
                url = 'http://192.168.103.17:3000/uploadImageWithName'
                r = requests.post(url, files=files)
            return result, rects,
        except Exception as e:
            print('template_matching: Error, ', e)
            return False, []

    '''
    def template_matching(self, img, template):
        result = False
        print("Frank: template_matching, {}, {}".format(template.shape, len(template.shape)))
        if len(template.shape) == 3:
            h, w, _ = template.shape
        else:
            h, w = template.shape
        print("template_matching: w={}, h={}".format(w, h))
        # All the 6 methods for comparison in a list
        #methods = ['cv.TM_CCOEFF', 'cv.TM_CCOEFF_NORMED', 'cv.TM_CCORR',
        #            'cv.TM_CCORR_NORMED', 'cv.TM_SQDIFF', 'cv.TM_SQDIFF_NORMED']
        methods = ['cv2.TM_CCOEFF_NORMED']
        img2 = img.copy()
        for meth in methods:
            img = img2.copy()
            method = eval(meth)
            # Apply template Matching
            res = cv2.matchTemplate(img,template,method)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
            # If the method is TM_SQDIFF or TM_SQDIFF_NORMED, take minimum
            if method in [cv2.TM_SQDIFF, cv2.TM_SQDIFF_NORMED]:
                top_left = min_loc
            else:
                top_left = max_loc
            bottom_right = (top_left[0] + w, top_left[1] + h)
            print('template_matching: top_left={}, bottom_right={}'.format(top_left, bottom_right))
            cv2.rectangle(img, top_left, bottom_right, 255, 2)
            x, y, w, h = top_left[0], top_left[1], bottom_right[0]-top_left[0], bottom_right[1]-top_left[1]
            if top_left is not None:
                result = True
        return result, [(x, y, w, h)]
    '''
