# coding=utf-8
"""An example of how to use your own dataset to train a classifier that recognizes people.
"""
# MIT License
#
# Copyright (c) 2016 David Sandberg
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import tensorflow as tf
import numpy as np
import argparse
import facenet
import os
import sys
import math
import pickle
from sklearn.svm import SVC
import heapq

first_loadmodel = False
last_modify_time = None
pkl_model = None
pkl_class_names = None
SVM_TRAIN_DUPLICATE_SMALL_DATASET=True

saved_model = None
saved_class_name = None
previous_model_ts = None

# PATH_TO_CKPT = 'facenet_models/20170512-110547/20170512-110547.pb'
#
# # Load a (frozen) Tensorflow model into memory.
# detection_graph = tf.Graph()
# with detection_graph.as_default():
#     od_graph_def = tf.GraphDef()
#     with tf.gfile.GFile(PATH_TO_CKPT, 'rb') as fid:
#         serialized_graph = fid.read()
#         od_graph_def.ParseFromString(serialized_graph)
#         tf.import_graph_def(od_graph_def, name='')
#
#
# detection_graph.as_default()
# sess = tf.Session(graph=detection_graph)
#
# # Get input and output tensors
# images_placeholder = detection_graph.get_tensor_by_name("input:0")
# embeddings = detection_graph.get_tensor_by_name("embeddings:0")
# phase_train_placeholder = detection_graph.get_tensor_by_name("phase_train:0")
# embedding_size = embeddings.get_shape()[1]


#def main(args):
# def facenet_svm(args):
#     np.random.seed(seed=args.seed)
#
#     if args.use_split_dataset:
#         dataset_tmp = facenet.get_dataset(args.data_dir)
#         train_set, test_set = split_dataset(dataset_tmp, args.min_nrof_images_per_class, args.nrof_train_images_per_class)
#         if (args.mode=='TRAIN'):
#             dataset = train_set
#         elif (args.mode=='CLASSIFY'):
#             dataset = test_set
#     else:
#         dataset = facenet.get_dataset(args.data_dir)
#
#     # Check that there are at least one training image per class
#     for cls in dataset:
#         assert(len(cls.image_paths)>0, 'There must be at least one image for each class in the dataset')
#
#
#     paths, labels = facenet.get_image_paths_and_labels(dataset)
#
#     print('Number of classes: %d' % len(dataset))
#     print('Number of images: %d' % len(paths))
#
#     # Load the model
#     print('Loading feature extraction model')
#     #facenet.load_model(args.model)
#
#     # # Get input and output tensors
#     # images_placeholder = tf.get_default_graph().get_tensor_by_name("input:0")
#     # embeddings = tf.get_default_graph().get_tensor_by_name("embeddings:0")
#     # phase_train_placeholder = tf.get_default_graph().get_tensor_by_name("phase_train:0")
#     # embedding_size = embeddings.get_shape()[1]
#
#     # Run forward pass to calculate embeddings
#     print('Calculating features for images')
#     nrof_images = len(paths)
#     nrof_batches_per_epoch = int(math.ceil(1.0*nrof_images / args.batch_size))
#     emb_array = np.zeros((nrof_images, embedding_size))
#     for i in range(nrof_batches_per_epoch):
#         start_index = i*args.batch_size
#         end_index = min((i+1)*args.batch_size, nrof_images)
#         paths_batch = paths[start_index:end_index]
#         images = facenet.load_data(paths_batch, False, False, args.image_size)
#         feed_dict = { images_placeholder:images, phase_train_placeholder:False }
#         emb_array[start_index:end_index,:] = sess.run(embeddings, feed_dict=feed_dict)
#
#     classifier_filename_exp = os.path.expanduser(args.classifier_filename)
#
#     if (args.mode=='TRAIN'):
#         # Train classifier
#         print('Training classifier')
#         model = SVC(kernel='linear', probability=True)
#         model.fit(emb_array, labels)
#
#         # Create a list of class names
#         class_names = [ cls.name.replace('_', ' ') for cls in dataset]
#         # class_names = [cls.name for cls in dataset]
#
#         # Saving classifier model
#         with open(classifier_filename_exp, 'wb') as outfile:
#             pickle.dump((model, class_names), outfile)
#         print('Saved classifier model to file "%s"' % classifier_filename_exp)
#
#     elif (args.mode=='CLASSIFY'):
#         global pkl_model
#         global pkl_class_names
#         # Classify images
#         print('Testing classifier')
#         if args.reload_pkl is True:
#             print("Reload .pkl file.")
#             with open(classifier_filename_exp, 'rb') as infile:
#                 (pkl_model, pkl_class_names) = pickle.load(infile)
#
#         print('Loaded classifier model from file "%s"' % classifier_filename_exp)
#
#         predictions = pkl_model.predict_proba(emb_array)
#         best_class_indices = np.argmax(predictions, axis=1)
#         best_class_probabilities = predictions[np.arange(len(best_class_indices)), best_class_indices]
#
#         for i in range(len(best_class_indices)):
#             print('%s' % paths_batch[i])
#             print('%4d  %s: %.3f' % (i, pkl_class_names[best_class_indices[i]], best_class_probabilities[i]))
#
#         score = best_class_probabilities[0]
#         accuracy = np.mean(np.equal(best_class_indices, labels))
#         print('Accuracy: %.3f' % accuracy)
#         if len(best_class_indices) > 0:
#             return 0, pkl_class_names[best_class_indices[0]], score
#         else:
#             return -1, None, 0
#

def classify(emb_array, classifier_filename):
    if not os.path.exists(classifier_filename):
        return -1, None, 0
    classifier_filename_exp = os.path.expanduser(classifier_filename)
    global previous_model_ts
    global saved_model
    global saved_class_name
    # Classify images

    print('Testing classifier')
    try:
        time_stamp_model = os.path.getmtime(classifier_filename_exp)
    except OSError:
        time_stamp_model = None

    if previous_model_ts != time_stamp_model or previous_model_ts is None:
        with open(classifier_filename_exp, 'rb') as infile:
            (saved_model, saved_class_name) = pickle.load(infile)
            print('Loaded classifier model from file "%s"' % classifier_filename_exp)
            previous_model_ts = time_stamp_model

    predictions = saved_model.predict_proba(emb_array)
    best_class_indices = np.argmax(predictions, axis=1)
    best_class_probabilities = predictions[np.arange(len(best_class_indices)), best_class_indices]

    # 实际使用的时候，每次分类只有一个目录，所以可以这么使用
    # score_list = []
    # for score in predictions[0]:
    #     score_list.append(score)

    #score_1, score_2 = heapq.nlargest(2, score_list, key=lambda x: x)  # 分类得分前两类的值

    #for i in range(len(best_class_indices)):
    #    print('%4d  %s: %.3f' % (i, saved_class_name[best_class_indices[i]], best_class_probabilities[i]))

    if len(best_class_indices) > 0:
        score = best_class_probabilities[0]
        return 0, saved_class_name[best_class_indices[0]], score
    else:
        return -1, None, 0


# def train_svm(args_list):
#     args = parse_arguments(args_list)
#     dataset = facenet.get_dataset(args.data_dir)
#     paths, labels = facenet.get_image_paths_and_labels(dataset)
#     nrof_images = len(paths)
#     nrof_batches_per_epoch = int(math.ceil(1.0*nrof_images / args.batch_size))
#     emb_array = np.zeros((nrof_images, embedding_size))
#     for i in range(nrof_batches_per_epoch):
#         start_index = i*args.batch_size
#         end_index = min((i+1)*args.batch_size, nrof_images)
#         paths_batch = paths[start_index:end_index]
#         images = facenet.load_data(paths_batch, False, False, args.image_size)
#         feed_dict = { images_placeholder:images, phase_train_placeholder:False }
#         emb_array[start_index:end_index,:] = sess.run(embeddings, feed_dict=feed_dict)
#     classifier_filename_exp = os.path.expanduser(args.classifier_filename)
#     if (args.mode=='TRAIN'):
#         # Train classifier
#         print('Training classifier')
#         model = SVC(kernel='linear', probability=True)
#         model.fit(emb_array, labels)
#
#         # Create a list of class names
#         class_names = [ cls.name.replace('_', ' ') for cls in dataset]
        # class_names = [cls.name for cls in dataset]
#
#         # Saving classifier model
#         with open(classifier_filename_exp, 'wb') as outfile:
#             pickle.dump((model, class_names), outfile)
#         print('Saved classifier model to file "%s"' % classifier_filename_exp)
def get_image_paths(facedir):
    image_paths = []
    if os.path.isdir(facedir):
        images = os.listdir(facedir)
        image_paths = [os.path.join(facedir,img) for img in images]
    return image_paths
class ImageClass():
    "Stores the paths to images for a given class"
    def __init__(self, name, image_paths):
        self.name = name
        self.image_paths = image_paths

    def __str__(self):
        return self.name + ', ' + str(len(self.image_paths)) + ' images'

    def __len__(self):
        return len(self.image_paths)
def get_image_paths_and_labels(dataset):
    image_paths_flat = []
    labels_flat = []
    for i in range(len(dataset)):
        image_paths_flat += dataset[i].image_paths
        labels_flat += [i] * len(dataset[i].image_paths)
    return image_paths_flat, labels_flat

def get_dataset(paths, has_class_directories=True):
    dataset = []
    for path in paths.split(':'):
        path_exp = os.path.expanduser(path)
        classes = os.listdir(path_exp)
        classes.sort()
        nrof_classes = len(classes)
        for i in range(nrof_classes):
            class_name = classes[i]
            facedir = os.path.join(path_exp, class_name)
            image_paths = get_image_paths(facedir)
            dataset.append(ImageClass(class_name, image_paths))

    return dataset

def get_traindataset(paths, has_class_directories=True):
    dataset = []
    for path in paths.split(':'):
        path_exp = os.path.expanduser(path)
        classes = os.listdir(path_exp)
        classes.sort()
        nrof_classes = len(classes)
        for i in range(nrof_classes):
            class_name = classes[i]
            facedir = os.path.join(path_exp, class_name)
            image_paths = get_trainimage_paths(facedir)
            dataset.append(ImageClass(class_name, image_paths))

    return dataset

def get_trainimage_paths(facedir):
    image_paths = []
    if os.path.isdir(facedir):
        images = os.listdir(facedir)
        image_paths = [os.path.join(facedir,img) for img in images]
        if len(images) < 35:
            count = len(images)
            min_training_count = 150
            while count < min_training_count:
                if count + len(images) > min_training_count:
                    cp_count = min_training_count - count
                else:
                    cp_count = len(images)
                image_paths += [os.path.join(facedir,images[n]) for n in range(0, cp_count)]
                count += cp_count
                if count >= min_training_count:
                    break
    print("len(images)=%d, len(image_paths) = %d" % (len(images), len(image_paths)))
    return image_paths

def train_svm_with_embedding(args_list):
    args = parse_arguments(args_list)
    if SVM_TRAIN_DUPLICATE_SMALL_DATASET is True:
        dataset = get_traindataset(args.data_dir)
    else:
        dataset = get_dataset(args.data_dir)
    paths, labels = get_image_paths_and_labels(dataset)
    if paths is None or labels is None:
        return "No Datasets"
    ready = False
    for label in labels:
        if label > 0:
            ready = True
            break
    if ready is False:
        return "No Enough Datasets. At least 2."

    nrof_images = len(paths)
    nrof_batches_per_epoch = int(math.ceil(1.0 * nrof_images / args.batch_size))

    emb_array = np.zeros((nrof_images, 128))
    for i in range(nrof_batches_per_epoch):
        start_index = i*args.batch_size
        end_index = min((i+1)*args.batch_size, nrof_images)
        paths_batch = paths[start_index:end_index]

        bottlenecks_list = []
        for bottleneck_path in paths_batch:
            with open(bottleneck_path, 'r') as bottleneck_file:
                bottleneck_string = bottleneck_file.read()
                # print(bottleneck_string)
            bottleneck_values = [float(x) for x in bottleneck_string.split(',')]
            # print(bottleneck_values)
            bottlenecks_list.append(bottleneck_values)

        embs = np.array(bottlenecks_list)
        emb_array[start_index:end_index,:] = embs

    classifier_filename_exp = os.path.expanduser(args.classifier_filename)
    if (args.mode=='TRAIN'):
        # Train classifier
        print('Training classifier')
        model = SVC(kernel='linear', probability=True)
        model.fit(emb_array, labels)

        # Create a list of class names
        class_names = [ cls.name.replace('_', ' ') for cls in dataset]
        # class_names = [cls.name for cls in dataset]

        # Saving classifier model
        with open(classifier_filename_exp, 'wb') as outfile:
            pickle.dump((model, class_names), outfile)
        print('Saved classifier model to file "%s"' % classifier_filename_exp)
    return "OK"

def split_dataset(dataset, min_nrof_images_per_class, nrof_train_images_per_class):
    train_set = []
    test_set = []
    for cls in dataset:
        paths = cls.image_paths
        # Remove classes with less than min_nrof_images_per_class
        if len(paths)>=min_nrof_images_per_class:
            np.random.shuffle(paths)
            train_set.append(facenet.ImageClass(cls.name, paths[:nrof_train_images_per_class]))
            test_set.append(facenet.ImageClass(cls.name, paths[nrof_train_images_per_class:]))
    return train_set, test_set


def parse_arguments(argv):
    parser = argparse.ArgumentParser()

    parser.add_argument('mode', type=str, choices=['TRAIN', 'CLASSIFY'],
        help='Indicates if a new classifier should be trained or a classification ' +
        'model should be used for classification', default='CLASSIFY')
    parser.add_argument('data_dir', type=str,
        help='Path to the data directory containing aligned LFW face patches.')
    parser.add_argument('model', type=str,
        help='Could be either a directory containing the meta_file and ckpt_file or a model protobuf (.pb) file')
    parser.add_argument('classifier_filename',
        help='Classifier model file name as a pickle (.pkl) file. ' +
        'For training this is the output and for classification this is an input.')
    parser.add_argument('--use_split_dataset',
        help='Indicates that the dataset specified by data_dir should be split into a training and test set. ' +
        'Otherwise a separate test set can be specified using the test_data_dir option.', action='store_true')
    parser.add_argument('--test_data_dir', type=str,
        help='Path to the test data directory containing aligned images used for testing.')
    parser.add_argument('--batch_size', type=int,
        help='Number of images to process in a batch.', default=90)
    parser.add_argument('--image_size', type=int,
        help='Image size (height, width) in pixels.', default=160)
    parser.add_argument('--seed', type=int,
        help='Random seed.', default=666)
    parser.add_argument('--min_nrof_images_per_class', type=int,
        help='Only include classes with at least this number of images in the dataset', default=20)
    parser.add_argument('--nrof_train_images_per_class', type=int,
        help='Use this number of images from each class for training and the rest for testing', default=10)

    return parser.parse_args(argv)


# def facenet_svm_main(args_list):
#     global last_modify_time
#     # global first_loadmodel
#     args = parse_arguments(args_list)
#     # if first_loadmodel is False:
#     #     facenet.load_model(args.model)
#     #     first_loadmodel = True
#     #     print('Reload pretrained facenet mode.')
#     stat_info = os.stat(args.classifier_filename)
#     modify_time = stat_info.st_mtime
#     if modify_time != last_modify_time:  # if pb was modified
#         last_modify_time = modify_time
#         args.reload_pkl = True
#         print('args.reload_pkl is True')
#     else:
#         args.reload_pkl = False
#         print('args.reload_pkl is False')
#     return facenet_svm(args)
#
#
# if __name__ == '__main__':
#     facenet_svm(parse_arguments(sys.argv[1:]))
