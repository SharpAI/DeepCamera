# coding=utf-8
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import face_detection as m
import json, cv2, os
import numpy as np
from scipy import misc
import face_preprocess
import time

minsize = int(os.getenv("MINIMAL_FACE_RESOLUTION", default="100"))  # minimum size of face, 100 for 1920x1080 resolution, 70 for 1280x720.
threads_number = int(os.getenv("THREADS_NUM_FACE_DETECTOR", default="1"))
image_size = 160
margin = 16
BLURY_THREHOLD = 5

m.init('./model')
m.set_minsize(minsize)
m.set_threshold(0.6,0.7,0.8)
m.set_num_threads(threads_number)

def get_filePath_fileName_fileExt(filename):
    (filepath,tempfilename) = os.path.split(filename)
    (shotname,extension) = os.path.splitext(tempfilename)
    return filepath, shotname, extension

def prewhiten(x):
    mean = np.mean(x)
    std = np.std(x)
    std_adj = np.maximum(std, 1.0/np.sqrt(x.size))
    y = np.multiply(np.subtract(x, mean), 1/std_adj)
    return y

def resize2square(x1, x2, y1, y2):
    w = x2 - x1
    h = y2 - y1
    delt = 0
    if w > h:
        delt = w -h
        return x1, x2, (y1 - int(delt/2)), (y2 + int(delt - delt/2))
    delt = h -w
    return (x1 - int(delt/2)), (x2 + int(delt - int(delt/2))), y1, y2

def faceBlury(gray_face):
    #gray_face = cv2.cvtColor(aligned_face, cv2.COLOR_BGR2GRAY)
    blury_value = cv2.Laplacian(gray_face, cv2.CV_64F).var()
    return blury_value

def faceStyle(landmark, bb, face_width):
    style = []

    eye_1 = landmark[0]
    eye_2 = landmark[1]
    nose = landmark[2]
    mouth_1 = landmark[3]
    mouth_2 = landmark[4]

    middle_point = (bb[2] + bb[0])/2
    y_middle_point = (bb[3] + bb[1]) / 2
    eye_distance = abs(eye_1[0]-eye_2[0])
    if eye_distance < 2:
        print('(Eye distance less than 2 pixels) Add style')
        style.append('side_face')
    elif eye_1[0] > middle_point:
        print('(Left Eye on the Right) Add style')
        style.append('left_side')
        # continue
    elif eye_2[0] < middle_point:
        print('(Right Eye on the left) Add style')
        style.append('right_side')
        # continue
    elif max(eye_1[1], eye_2[1]) > y_middle_point:
        print('(Eye lower than middle of face) Skip')
        style.append('lower_head')
    elif face_width/eye_distance > 6:
        print('side_face, eye distance is {}, face width is {}'.format(eye_distance,face_width))
        style.append('side_face')
    #elif nose[1] < y_middle_point:
    #    # 鼻子的y轴高于图片的中间高度，就认为是抬头
    #    style.append('raise_head')
    else:
        style.append('front')
    return style

def load_align_image(result, image_path, trackerid, ts, cameraId):
    detected = False
    people_cnt = 0
    cropped = []
    nrof_faces = 0

    if result is None or len(result['result']) < 1:
        return None, None, None, None

    results = result['result']
    if results is None or len(results) < 1:
        return None, None, None, None

    face_path = {}
    blury_arr = {}
    imgs_style = {}

    img = misc.imread(image_path)
    img_size = np.asarray(img.shape)[0:2]
    img_w = img_size[1]
    img_h = img_size[0]

    for i in range(len(results)):
        item     = results[i]
        landmark = item['landmark']
        score    = item['score']
        bbox     = item['bbox']
        x1, y1, x2, y2 = bbox

        x1, x2, y1, y2 = resize2square(x1, x2, y1, y2)
        if x1 <= 0 or y1 <= 0 or x2 >= img_w or y2 >= img_h:
            print('Out of boundary ({},{},{},{})'.format(x1, y1, x2, y2))
            continue

        face_width  = x2 - x1
        face_height = y2 - y1

        if face_width * face_height  < minsize * minsize:
            print("to small to recognise ({},{})".format(face_width,face_height))
            continue

        #style
        style = faceStyle(landmark, bbox, face_width)

        #blury
        cropped = img[y1:y2, x1:x2, :]
        aligned = misc.imresize(cropped, (160, 160), interp='bilinear')

        # Need to detect if face is too blury to be detected
        blury_value = faceBlury(aligned)
        print(blury_value)
        if blury_value < BLURY_THREHOLD:
            print('A blur face (%d) captured, avoid it.' %blury_value)
            style = ['blury']
        else:
            print('Blur Value: %d, good'%blury_value)

        new_image_path = image_path.rsplit('.', 1)[0] + '_' + str(i) + '.' + 'png'
        np.save(new_image_path, aligned)
        #print('image path saved aligned: ', new_image_path)
        prewhitened = prewhiten(aligned)
        face_path[new_image_path] = prewhitened
        blury_arr[new_image_path] = blury_value
        imgs_style[new_image_path] = '|'.join(style)

    return len(results), face_path, imgs_style, blury_arr

def load_align_image_v2(result, image_path, trackerid, ts, cameraId, face_filter):
    detected = False
    people_cnt = 0
    cropped = []
    nrof_faces = 0

   # if result is None or len(result['result']) < 1:
   #     return None, None, None, None

    results = result['result']
    if results is None or len(results) < 1:
        return None, None, None, None, None, None

    face_path = {}
    blury_arr = {}
    imgs_style = {}
    face_width_list = {}
    face_height_list = {}

    img = misc.imread(image_path)
    img_size = np.asarray(img.shape)[0:2]
    img_w = img_size[1]
    img_h = img_size[0]

    for i in range(len(results)):
        item     = results[i]
        landmark = item['landmark']
        score    = item['score']
        bbox     = item['bbox']
        #if bbox.shape[0] == 0:
        #  return None
        #print("bbox {}--- {}, landmark {} ----- {}".format(type(bbox), bbox,type(landmark),landmark))

        x1, y1, x2, y2 = bbox
        if x1 <= 0 or y1 <= 0 or x2 >= img_w or y2 >= img_h:
            print('Out of boundary ({},{},{},{})'.format(x1, y1, x2, y2))
            continue
        face_width  = x2 - x1
        face_height = y2 - y1

        if face_width * face_height  < minsize * minsize:
            print("to small to recognise ({},{})".format(face_width,face_height))
            continue

        #Check if face is misrecognized
        if face_filter is not None:
            box = (x1, y1, x2, y2)
            #crop = img[bb[1]:(bb[3]+bb[1]), bb[0]:(bb[2]+bb[0]), :]
            cropped = img[y1:y2, x1:x2, :]
            star_time = time.time()
            result, rects = face_filter.template_matching(cameraId, cropped, box, image_path)
            end_time = time.time()
            print('Performance: template_matching is {}S'.format(end_time-star_time))
            if result is False:
                print('filter_face: template_matching is False.')
            else:
                print('filter_face: template_matching is True.')
                continue
        else:
            print('face_filter is None, disabled by environment')

        #style
        style = faceStyle(landmark, bbox, face_width)

        #face_preprocess
        bbox = x1, x2, y1, y2
        bbox_nparr = np.array(bbox, dtype=np.float64)
        points_nparr = np.array(landmark, dtype=np.int32).flatten()
        points_nparr = points_nparr.reshape((5,2))
        nimg = face_preprocess.preprocess(image_path, bbox_nparr, points_nparr, image_size='112,112')

        # Need to detect if face is too blury to be detected
        blury_value = faceBlury(nimg)

        new_image_path = image_path.rsplit('.', 1)[0] + '_' + str(i) + '.' + 'png'
        misc.imsave(new_image_path, nimg)
        if blury_value < BLURY_THREHOLD:
            print('A blur face (%d) captured, avoid it.' %blury_value)
            style = ['blury']
        else:
            print('Blur Value: %d, good'%blury_value)

        #FIXME: BGR2RGB ??
        #nimg = cv2.cvtColor(nimg, cv2.COLOR_BGR2RGB)
        #aligned = np.transpose(nimg, (2,0,1))

        #print('img aligned savepath: ',new_np_path)
        #prewhitened = prewhiten(aligned_img)
        face_path[new_image_path] = None
        blury_arr[new_image_path] = blury_value
        imgs_style[new_image_path] = '|'.join(style)
        face_width_list[new_image_path] = face_width
        face_height_list[new_image_path] = face_height

    return len(face_path), face_path, imgs_style, blury_arr, face_width_list, face_height_list

def detect(image_path, trackerid, ts, cameraId, face_filter):
    result = m.detect(image_path)

    #FIXME:
    result = result.replace('[,', '[')
    result = json.loads(result)
    #print('detect result-----',result)
    people_cnt = 0
    cropped = []
    detected = False

    nrof_faces, img_data, imgs_style, blury_arr, face_width, face_height = load_align_image_v2(result, image_path, trackerid, ts, cameraId, face_filter)
    if img_data is not None and len(img_data) > 0:
        people_cnt = len(img_data)
        detected = True
        for align_image_path, prewhitened in img_data.items():
            style=imgs_style[align_image_path]
            blury=blury_arr[align_image_path]
            width=face_width[align_image_path]
            height=face_height[align_image_path]
            cropped.append({"path": align_image_path, "style": style, "blury": blury, "ts": ts,
                "trackerid": trackerid, "totalPeople": people_cnt, "cameraId": cameraId,
                "width":width,"height":height})

    return json.dumps({'detected': detected, "ts": ts, "totalPeople": people_cnt, "cropped": cropped, 'totalmtcnn': nrof_faces})
