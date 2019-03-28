# -*- coding: UTF-8 -*-
import time
import tensorflow as tf
import os
import shutil
import cv2
import numpy as np
import matplotlib.pyplot as plt
# %pylab inline
from scipy import misc

from align import detect_face


minsize = 20  # minimum size of face
threshold = [0.6, 0.7, 0.7]  # three steps's threshold
factor = 0.709  # scale factor
# sess, graph = FaceProcessing.InitialFaceProcessor()\

BASEPATH = os.path.abspath(os.getenv('RUNTIME_BASEDIR',os.path.dirname(__file__)))

graph2 = tf.Graph()
with graph2.as_default():
    sess2 = tf.Session(config=tf.ConfigProto(log_device_placement=False), graph=graph2)
    with sess2.as_default():
        pnet, rnet, onet = detect_face.create_mtcnn(sess2, None)


def load_align_image(image_path, sess, graph, pnet, rnet, onet):
    img = misc.imread(os.path.expanduser(image_path))

    with graph2.as_default():
        # sess2 = tf.Session(config=tf.ConfigProto(log_device_placement=False))
        with sess2.as_default():
            bounding_boxes, bounding_points = detect_face.detect_face(img, minsize, pnet, rnet, onet, threshold,
                                                                            factor)
    nrof_faces = bounding_boxes.shape[0]  # 人脸数目
    print('The number of faces detected： {}'.format(nrof_faces))


def imshow(image_path):
    img = misc.imread(image_path)
    img_size = np.asarray(img.shape)[0:2]

    bounding_boxes, bounding_points = detect_face.detect_face(img, minsize, pnet, rnet, onet, threshold,factor)
    # img_color = cv2.imread(image_path)
    crop_faces = []
    for i in range(bounding_boxes.shape[0]):  # 人脸数目:
        draw = img.copy()

        det = np.squeeze(detect_face.rerec(bounding_boxes.copy())[i, 0:4])
        bounding_point = bounding_points[:, i]  # 按i获取多个人脸的point
        print(det)
        print(bounding_point)
        bb = np.zeros(4, dtype=np.int32)  # 坐标
        bb[0] = np.maximum(det[0] - 2 / 2, 0)
        bb[1] = np.maximum(det[1] - 2 / 2, 0)
        bb[2] = np.minimum(det[2] + 2 / 2, img_size[1])
        bb[3] = np.minimum(det[3] + 2 / 2, img_size[0])

        for ii in range(5):
            cv2.circle(draw, (bounding_point[ii], bounding_point[ii + 5]), 1, (255, 0, 0), 2)  # 绘制特征点

        cropped = draw[bb[1]:bb[3], bb[0]:bb[2], :]

        aligned = misc.imresize(cropped, (160, 160), interp='bilinear')  # 缩放图像

        print(aligned.shape)
        crop_faces.append(aligned)
        # plt.imshow(aligned)
        plt.imshow(draw)
        plt.show()
    #
    # plt.imshow(img)
    # plt.show()


def detect_folder(folder, threshold):
    face_counts = 0
    n_time = time.time()
    total_set = set()
    for img_path in os.listdir(folder):
        img_path = os.path.join(folder, img_path)
        img = misc.imread(os.path.expanduser(img_path))
        # load_align_image(img, sess, graph, pnet, rnet, onet)
        bounding_boxes, bounding_points = detect_face.detect_face(img, minsize, pnet, rnet, onet, threshold,
                                factor)
        nrof_faces = bounding_boxes.shape[0]  # 人脸数目
        face_counts += nrof_faces
        total_set.add((img_path, nrof_faces))
        print('{}, The number of faces detected： {}'.format(img_path, nrof_faces))
    print('Total faces: {}; cotst: {} '.format(face_counts, time.time()-n_time))
    return total_set


def save_align_image(image_path):
    img = misc.imread(os.path.expanduser(image_path))
    img_size = np.asarray(img.shape)[0:2]
    with graph2.as_default():
        # sess2 = tf.Session(config=tf.ConfigProto(log_device_placement=False))
        with sess2.as_default():
            bounding_boxes, bounding_points = detect_face.detect_face(img, minsize, pnet, rnet, onet, threshold, factor)
    nrof_faces = bounding_boxes.shape[0]  # 人脸数目
    width = img_size[1]
    height = img_size[0]
    for i in range(nrof_faces):  # 遍历所有faces
        draw = img.copy()
        print('nrof_faces: {}'.format(i))
        # det = np.squeeze(bounding_boxes[i, 0:4])
        det = np.squeeze(detect_face.rerec(bounding_boxes.copy())[i, 0:4])
        bounding_point = bounding_points[:, i]  # 按i获取多个人脸的point
        bb = np.zeros(4, dtype=np.int32)  # 坐标
        bb[0] = np.maximum(det[0] - 2 / 2, 0)
        bb[1] = np.maximum(det[1] - 2 / 2, 0)
        bb[2] = np.minimum(det[2] + 2 / 2, img_size[1])
        bb[3] = np.minimum(det[3] + 2 / 2, img_size[0])

        # for ii in range(5):
        #    cv2.circle(draw, (bounding_point[ii], bounding_point[ii + 5]), 1, (255, 0, 0), 2)  # 绘制特征点


        cropped = draw[bb[1]:bb[3], bb[0]:bb[2], :]  # 裁剪
        aligned = misc.imresize(cropped, (160, 160), interp='bilinear')  # 缩放图像

        # plt.imshow(aligned)
        # plt.show()

        # # Need to detect if face is too blury to be detected
        # gray_face = cv2.cvtColor(aligned, cv2.COLOR_BGR2GRAY)
        # blury_value = cv2.Laplacian(gray_face, cv2.CV_64F).var()
        # if blury_value < 4:
        #     print('A blur face (%d) captured, avoid it.' %blury_value)
        #     continue
        # else:
        #     print('Blur Value: %d, good'%blury_value)
        #
        base_path, old_dir_name, img_name = image_path.rsplit('/', 2)
        new_dir_name = old_dir_name + '_'
        new_dir_path = os.path.join(base_path, new_dir_name)
        new_img_path = os.path.join(new_dir_path, img_name)
        if not os.path.exists(new_dir_path):
            os.mkdir(new_dir_path)
        misc.imsave(new_img_path, aligned)  # 保存为图像


def category_style(image_path):
    img = misc.imread(image_path)
    img_size = np.asarray(img.shape)[0:2]
    width = img_size[1]
    height = img_size[0]

    bounding_boxes, bounding_points = detect_face.detect_face(img, minsize, pnet, rnet, onet, threshold,factor)
    # img_color = cv2.imread(image_path)
    crop_faces = []
    for i in range(bounding_boxes.shape[0]):  # 人脸数目:
        draw = img.copy()

        det = np.squeeze(detect_face.rerec(bounding_boxes.copy())[i, 0:4])
        # det = np.squeeze(bounding_boxes[i, 0:4])
        bounding_point = bounding_points[:, i]  # 按i获取多个人脸的point
        print(det)
        print(bounding_point)
        bb = np.zeros(4, dtype=np.int32)  # 坐标
        bb[0] = np.maximum(det[0] - 2 / 2, 0)
        bb[1] = np.maximum(det[1] - 2 / 2, 0)
        bb[2] = np.minimum(det[2] + 2 / 2, img_size[1])
        bb[3] = np.minimum(det[3] + 2 / 2, img_size[0])
        # if bb[0] == 0 or bb[1] == 0 or bb[2] >= width or bb[3] >= height:
        if False:
            style = 'out'
            print('Out of boundary')
        else:
            eye_1 = [bounding_point[0], bounding_point[5]]
            eye_2 = [bounding_point[1], bounding_point[6]]
            face_width = bb[2] - bb[0]
            face_height = bb[3] - bb[1]
            print('Face width is {}'.format(face_width))
            print('Face height is {}'.format(face_height))
            if face_width < 50 or face_height < 50:
                print("to small to recognise")
                style = 'low_pixel'
            else:
                middle_point = (bb[2] + bb[0]) / 2
                y_middle_point = (bb[3] + bb[1]) / 2
                if eye_1[0] > middle_point:
                    print('(Left Eye on the Right) Middle point is larger than middle point, must be an angling face')
                    style = 'left_side'
                    # continue
                elif eye_2[0] < middle_point:
                    print('(Right Eye on the left) Middle point is larger than middle point, must be an angling face')
                    style = 'right_side'
                    # continue
                elif max(bounding_point[5], bounding_point[6]) > y_middle_point:
                    # 左右两个眼睛最低的y轴，低于图片的中间高度，就认为是低头
                    style = 'lower_head'
                elif bounding_point[7] < y_middle_point:
                    # 鼻子的y轴高于图片的中间高度，就认为是抬头
                    style = 'raise_head'
                else:
                    style = 'front'

            # 分类保存
        base_path ,old_dir_name, img_name = image_path.rsplit('/', 2)
        new_dir_name = old_dir_name + '_' + style
        new_dir_path = os.path.join(base_path, new_dir_name)
        new_img_path = os.path.join(new_dir_path, img_name)
        if not os.path.exists(new_dir_path):
            os.mkdir(new_dir_path)
        shutil.copyfile(image_path, new_img_path)


if __name__ == '__main__':
    """
    输入同一个目录，计算不同的阈值下，检测出人脸数的差别
    """
    # s1 = detect_folder('/home/actiontec/PycharmProjects/dl_test/FACE_DATASET/ALL/dioris', [0.6, 0.7, 0.7])
    # s2 = detect_folder('/home/actiontec/PycharmProjects/dl_test/FACE_DATASET/ALL/dioris', [0.6, 0.7, 0.97])
    # print(s1 ^ s2)
    # imshow('/home/actiontec/PycharmProjects/dl_test/face_detect/image/e5354038-68c5-11e7-980e-8844774fed1f.jpg')
    folder = '/home/actiontec/PycharmProjects/dl_test/FACE_DATASET/face/yrp'
    for path in os.listdir(folder):
        img_path = os.path.join(folder, path)
        save_align_image(img_path)
