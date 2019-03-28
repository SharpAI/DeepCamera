# coding=utf-8
from __future__ import absolute_import, print_function

import hashlib
import os
import os.path
import random
import re
import struct
import sys
import tarfile
from datetime import datetime
from time import time

import numpy as np
#import tensorflow as tf
from six.moves import urllib
#from tensorflow.python.framework import graph_util, tensor_shape
#from tensorflow.python.platform import gfile
#from tensorflow.python.util import compat
from urllib import urlopen
from PIL import Image

BASEPATH = os.path.abspath(os.getenv('RUNTIME_BASEDIR',os.path.dirname(__file__)))

image_dir = os.path.join("Animal_Data")
output_graph = "bottlenecks_graph.pb"
output_labels = "output_labels.txt"
summaries_dir = "/tmp/output_labels.txt"
how_many_training_steps = 500
learning_rate = 0.01
testing_percentage = 10
validation_percentage = 10
eval_step_interval = 10
train_batch_size = 100
test_batch_size = -1
validation_batch_size = 100
print_misclassified_test_images = False
model_dir = os.path.join('utilspb')
bottleneck_dir = "bottlenecks"
final_tensor_name = "final_result"
flip_left_right = False
random_crop = 0
random_scale = 0
random_brightness = 0
DATA_URL = 'http://download.tensorflow.org/models/image/imagenet/inception-2015-12-05.tgz'

# pylint: enable=line-too-long
BOTTLENECK_TENSOR_NAME = 'pool_3/_reshape:0'
BOTTLENECK_TENSOR_SIZE = 2048
MODEL_INPUT_WIDTH = 299
MODEL_INPUT_HEIGHT = 299
MODEL_INPUT_DEPTH = 3
JPEG_DATA_TENSOR_NAME = 'DecodeJpeg/contents:0'
RESIZED_INPUT_TENSOR_NAME = 'ResizeBilinear:0'
MAX_NUM_IMAGES_PER_CLASS = 2 ** 27 - 1  # ~134M

image_counter = 0
start_time = None

# BASE_FOLDER = os.path.join(os.getenv('RUNTIME_BASEDIR',os.path.abspath(os.path.dirname(__file__))), 'dataset')
# BOTTLENECKS_FOLDER = os.path.join(os.getenv('RUNTIME_BASEDIR',os.path.abspath(os.path.dirname(__file__))), 'bottlenecks')
g_graph=None
g_bottleneck_tensor=None
g_jpeg_data_tensor=None
g_resized_image_tensor=None

size = (299, 299)


def create_image_lists(image_dir, testing_percentage, validation_percentage):
    if not gfile.Exists(image_dir):
        print("Image directory '" + image_dir + "' not found.")
        return None
    result = {}
    sub_dirs = [x[0] for x in gfile.Walk(image_dir)]
    # The root directory comes first, so skip it.
    is_root_dir = True
    for sub_dir in sub_dirs:
        if is_root_dir:
            is_root_dir = False
            continue
        extensions = ['jpg', 'jpeg', 'JPG', 'JPEG']
        file_list = []
        dir_name = os.path.basename(sub_dir)
        if dir_name == image_dir:
            continue
        print("Looking for images in '" + dir_name + "'")
        for extension in extensions:
            file_glob = os.path.join(image_dir, dir_name, '*.' + extension)
            file_list.extend(gfile.Glob(file_glob))
        if not file_list:
            print('No files found')
            continue
        if len(file_list) < 20:
            print('WARNING: Folder has less than 20 images, which may cause issues.')
        elif len(file_list) > MAX_NUM_IMAGES_PER_CLASS:
            print('WARNING: Folder {} has more than {} images. Some images will '
                  'never be selected.'.format(dir_name, MAX_NUM_IMAGES_PER_CLASS))
        #label_name = re.sub(r'[^A-Za-z0-9_]+', ' ', dir_name.lower())
        label_name = dir_name
        training_images = []
        testing_images = []
        validation_images = []
        for file_name in file_list:
            base_name = os.path.basename(file_name)
            # We want to ignore anything after '_nohash_' in the file name when
            # deciding which set to put an image in, the data set creator has a way of
            # grouping photos that are close variations of each other. For example
            # this is used in the plant disease data set to group multiple pictures of
            # the same leaf.
            hash_name = re.sub(r'_nohash_.*$', '', file_name)
            # This looks a bit magical, but we need to decide whether this file should
            # go into the training, testing, or validation sets, and we want to keep
            # existing files in the same set even if more files are subsequently
            # added.
            # To do that, we need a stable way of deciding based on just the file name
            # itself, so we do a hash of that and then use that to generate a
            # probability value that we use to assign it.
            hash_name_hashed = hashlib.sha1(
                compat.as_bytes(hash_name)).hexdigest()
            percentage_hash = ((int(hash_name_hashed, 16) %
                                (MAX_NUM_IMAGES_PER_CLASS + 1)) *
                               (100.0 / MAX_NUM_IMAGES_PER_CLASS))
            if percentage_hash < validation_percentage:
                validation_images.append(base_name)
            elif percentage_hash < (testing_percentage + validation_percentage):
                testing_images.append(base_name)
            else:
                training_images.append(base_name)
        result[label_name] = {
            'dir': dir_name,
            'training': training_images,
            'testing': testing_images,
            'validation': validation_images,
        }
    return result


def get_image_path(image_lists, label_name, index, image_dir, category):
    if label_name not in image_lists:
        tf.logging.fatal('Label does not exist %s.', label_name)
    label_lists = image_lists[label_name]
    if category not in label_lists:
        tf.logging.fatal('Category does not exist %s.', category)
    category_list = label_lists[category]
    if not category_list:
        tf.logging.fatal('Label %s has no images in the category %s.',
                         label_name, category)
    mod_index = index % len(category_list)
    base_name = category_list[mod_index]
    sub_dir = label_lists['dir']
    full_path = os.path.join(image_dir, sub_dir, base_name)
    return full_path


def get_bottleneck_path(image_lists, label_name, index, bottleneck_dir,
                        category):

    return get_image_path(image_lists, label_name, index, bottleneck_dir,
                          category) + '.txt'


def create_inception_graph():
    with tf.Session() as sess:
        model_filename = os.path.join(model_dir, 'def.pb')
        if not os.path.exists(model_filename):
            model_filename = os.path.join(model_dir, 'classify_image_graph_def.pb')

        with gfile.FastGFile(model_filename, 'rb') as f:
            graph_def = tf.GraphDef()
            graph_def.ParseFromString(f.read())
            bottleneck_tensor, jpeg_data_tensor, resized_input_tensor = (
                tf.import_graph_def(graph_def, name='', return_elements=[
                    BOTTLENECK_TENSOR_NAME, JPEG_DATA_TENSOR_NAME,
                    RESIZED_INPUT_TENSOR_NAME]))
    return sess, sess.graph, bottleneck_tensor, jpeg_data_tensor, resized_input_tensor


def run_bottleneck_on_image(sess, image_data, image_data_tensor,
                            bottleneck_tensor):
    bottleneck_values = sess.run(
        bottleneck_tensor,
        {image_data_tensor: image_data})
    bottleneck_values = np.squeeze(bottleneck_values)
    return bottleneck_values



def resize(infile):
    """
    :param infile: 输入文件名
    :return: 保存调整大小后的图片到目录中
    """
    outfile = os.path.splitext(infile)[0] + "_resized.jpg"
    if infile != outfile:
        try:
            im = Image.open(infile)
            im.thumbnail(size, Image.ANTIALIAS)
            old_im_size = im.size

            ## By default, black colour would be used as the background for padding!
            new_im = Image.new("RGB", size)

            new_im.paste(im, ((size[0] - old_im_size[0]) / 2,
                              (size[1] - old_im_size[1]) / 2))

            new_im.save(outfile, "JPEG")
            return outfile
        except IOError:
            print("Cannot resize '%s'" % infile)
