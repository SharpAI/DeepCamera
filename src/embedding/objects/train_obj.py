from __future__ import absolute_import, division, print_function

import hashlib
import os
import requests
import os.path
import random
import re
import struct
import sys
import tarfile
from datetime import datetime
from time import time

import numpy as np
import tensorflow as tf
from tensorflow.python.framework import graph_util, tensor_shape
from tensorflow.python.platform import gfile
from tensorflow.python.util import compat

# path = os.path.join((os.path.abspath(os.path.pardir)))
# sys.path.append(path)
# from utilslib.save2gst import sendMessage2Group

def sendMessage2Group(uuid, group_id, text):
    if (len(uuid) < 1) or (len(group_id) < 1) or (len(text) < 1):
        return

    gst_api_url = 'http://workaihost.tiegushi.com/restapi/workai-send2group'
    #gst_api_url = 'http://192.168.1.73:3000/restapi/workai-send2group'
    payload = {'uuid': uuid,
               'group_id': group_id,
               'type': 'text',
               'text': text,
               'ts': int(time())*1000
               }
    try:
        requests.post(gst_api_url, data=payload, timeout=4)
    except Exception as e:
        print(e)


# image_dir = os.path.join("dataset")
# bottleneck_dir = "bottlenecks"

BASEPATH = os.path.abspath(os.getenv('RUNTIME_BASEDIR',os.path.dirname(__file__)))
# image_dir = os.path.join(os.getenv('RUNTIME_BASEDIR',os.path.abspath(os.path.dirname(__file__))), 'dataset')
# bottleneck_dir = os.path.join(os.getenv('RUNTIME_BASEDIR',os.path.abspath(os.path.dirname(__file__))), 'bottlenecks')

output_graph = "bottlenecks_graph.pb"
output_labels = "output_labels.txt"
summaries_dir = "/tmp/output_labels.txt"
how_many_training_steps = 300
learning_rate = 0.01
testing_percentage = 10
validation_percentage = 10
eval_step_interval = 10
train_batch_size = 100
test_batch_size = -1
validation_batch_size = 100
print_misclassified_test_images = False
model_dir = os.path.join('utilspb')
final_tensor_name = "final_result"
flip_left_right = False
random_crop = 0
random_scale = 0
random_brightness = 0

# pylint: enable=line-too-long
BOTTLENECK_TENSOR_SIZE = 2048
MODEL_INPUT_WIDTH = 299
MODEL_INPUT_HEIGHT = 299
MODEL_INPUT_DEPTH = 3
RESIZED_INPUT_TENSOR_NAME = 'ResizeBilinear:0'
MAX_NUM_IMAGES_PER_CLASS = 2 ** 27 - 1  # ~134M

image_counter = 0


def create_image_lists(image_dir, testing_percentage, validation_percentage):
    print('start create_image_lists')
    print(image_dir)
    if not gfile.Exists(image_dir):
        print("Image directory '" + image_dir + "' not found.")
        # return None
    result = {}
    sub_dirs = [x[0] for x in gfile.Walk(image_dir)]
    print(sub_dirs)
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
            continue
        elif len(file_list) > MAX_NUM_IMAGES_PER_CLASS:
            print('WARNING: Folder {} has more than {} images. Some images will '
                  'never be selected.'.format(dir_name, MAX_NUM_IMAGES_PER_CLASS))
        #label_name = re.sub(r'[^A-Za-z0-9_]+', ' ', dir_name.lower())
        label_name = dir_name
        training_images = []
        testing_images = []
        validation_images = []
        for i, file_name in enumerate(file_list):
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
            if i == 0:
                testing_images.append(base_name)
                validation_images.append(base_name)
                training_images.append(base_name)
            elif i == 1:
                validation_images.append(base_name)
            else:
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


def ensure_dir_exists(dir_name):
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)


def write_list_of_floats_to_file(list_of_floats, file_path):
    s = struct.pack('d' * BOTTLENECK_TENSOR_SIZE, *list_of_floats)
    with open(file_path, 'wb') as f:
        f.write(s)


def read_list_of_floats_from_file(file_path):
    with open(file_path, 'rb') as f:
        s = struct.unpack('d' * BOTTLENECK_TENSOR_SIZE, f.read())
        return list(s)


bottleneck_path_2_bottleneck_values = {}
# time_taken is in seconds
#hours, rest = divmod(time_taken,3600)
#minutes, seconds = divmod(rest, 60)


def get_bottleneck(sess, image_lists, label_name, index, image_dir,
                   category, bottleneck_dir):
    label_lists = image_lists[label_name]
    sub_dir = label_lists['dir']
    sub_dir_path = os.path.join(bottleneck_dir, sub_dir)
    ensure_dir_exists(sub_dir_path)
    bottleneck_path = get_bottleneck_path(
        image_lists, label_name, index, bottleneck_dir, category)
    with open(bottleneck_path, 'r') as bottleneck_file:
        bottleneck_string = bottleneck_file.read()
    did_hit_error = False
    try:
        bottleneck_values = [float(x) for x in bottleneck_string.split(',')]
    except:
        print("Invalid float found, recreating bottleneck")
        did_hit_error = True
    if did_hit_error:
        return None
    return bottleneck_values


def cache_bottlenecks(sess, image_lists, image_dir, bottleneck_dir):
    how_many_bottlenecks = 0
    ensure_dir_exists(bottleneck_dir)
    for label_name, label_lists in image_lists.items():
        for category in ['training', 'testing', 'validation']:
            category_list = label_lists[category]
            for index, unused_base_name in enumerate(category_list):
                bottleneck = get_bottleneck(sess, image_lists, label_name, index,
                                            image_dir, category, bottleneck_dir)
                if bottleneck:
                    how_many_bottlenecks += 1
                if how_many_bottlenecks % 100 == 0:
                    print(str(how_many_bottlenecks) +
                          ' bottleneck files created.')


def get_random_cached_bottlenecks(sess, image_lists, how_many, category,
                                  bottleneck_dir, image_dir):
    class_count = len(image_lists.keys())
    bottlenecks = []
    ground_truths = []
    filenames = []
    if how_many >= 0:
        # Retrieve a random sample of bottlenecks.
        for unused_i in range(how_many):
            label_index = random.randrange(class_count)
            label_name = list(image_lists.keys())[label_index]
            image_index = random.randrange(MAX_NUM_IMAGES_PER_CLASS + 1)
            image_name = get_image_path(image_lists, label_name, image_index,
                                        image_dir, category)
            bottleneck = get_bottleneck(sess, image_lists, label_name,
                                        image_index, image_dir, category,
                                        bottleneck_dir)
            if bottleneck:
                ground_truth = np.zeros(class_count, dtype=np.float32)
                ground_truth[label_index] = 1.0
                bottlenecks.append(bottleneck)
                ground_truths.append(ground_truth)
                filenames.append(image_name)
    else:
        # Retrieve all bottlenecks.
        for label_index, label_name in enumerate(image_lists.keys()):
            for image_index, image_name in enumerate(
                    image_lists[label_name][category]):
                image_name = get_image_path(image_lists, label_name, image_index,
                                            image_dir, category)
                bottleneck = get_bottleneck(sess, image_lists, label_name,
                                            image_index, image_dir, category,
                                            bottleneck_dir)
                if bottleneck:
                    ground_truth = np.zeros(class_count, dtype=np.float32)
                    ground_truth[label_index] = 1.0
                    bottlenecks.append(bottleneck)
                    ground_truths.append(ground_truth)
                    filenames.append(image_name)
    return bottlenecks, ground_truths, filenames


def should_distort_images(flip_left_right, random_crop, random_scale,
                          random_brightness):
    return (flip_left_right or (random_crop != 0) or (random_scale != 0) or
            (random_brightness != 0))


def variable_summaries(var):

    with tf.name_scope('summaries'):
        mean = tf.reduce_mean(var)
        tf.summary.scalar('mean', mean)
        with tf.name_scope('stddev'):
            stddev = tf.sqrt(tf.reduce_mean(tf.square(var - mean)))
        tf.summary.scalar('stddev', stddev)
        tf.summary.scalar('max', tf.reduce_max(var))
        tf.summary.scalar('min', tf.reduce_min(var))
        tf.summary.histogram('histogram', var)


def add_final_training_ops(class_count, final_tensor_name):

    with tf.name_scope('input'):
        bottleneck_input = tf.placeholder(tf.float32, shape=[
                                          None, BOTTLENECK_TENSOR_SIZE], name='BottleneckInputPlaceholder')
        ground_truth_input = tf.placeholder(tf.float32,
                                            [None, class_count],
                                            name='GroundTruthInput')
    # Organizing the following ops as `final_training_ops` so they're easier
    # to see in TensorBoard
    layer_name = 'final_training_ops'
    with tf.name_scope(layer_name):
        with tf.name_scope('weights'):
            layer_weights = tf.Variable(tf.truncated_normal(
                [BOTTLENECK_TENSOR_SIZE, class_count], stddev=0.001), name='final_weights')
            variable_summaries(layer_weights)
        with tf.name_scope('biases'):
            layer_biases = tf.Variable(
                tf.zeros([class_count]), name='final_biases')
            variable_summaries(layer_biases)
        with tf.name_scope('Wx_plus_b'):
            logits = tf.matmul(bottleneck_input, layer_weights) + layer_biases
            tf.summary.histogram('pre_activations', logits)
    final_tensor = tf.nn.softmax(logits, name=final_tensor_name)
    tf.summary.histogram('activations', final_tensor)
    with tf.name_scope('cross_entropy'):
        cross_entropy = tf.nn.softmax_cross_entropy_with_logits(
            labels=ground_truth_input, logits=logits)
        with tf.name_scope('total'):
            cross_entropy_mean = tf.reduce_mean(cross_entropy)
    tf.summary.scalar('cross_entropy', cross_entropy_mean)
    with tf.name_scope('train'):
        train_step = tf.train.GradientDescentOptimizer(learning_rate).minimize(
            cross_entropy_mean)
    return (train_step, cross_entropy_mean, bottleneck_input, ground_truth_input,
            final_tensor)


def add_evaluation_step(result_tensor, ground_truth_tensor):
    with tf.name_scope('accuracy'):
        with tf.name_scope('correct_prediction'):
            prediction = tf.argmax(result_tensor, 1)
            correct_prediction = tf.equal(
                prediction, tf.argmax(ground_truth_tensor, 1))
        with tf.name_scope('accuracy'):
            evaluation_step = tf.reduce_mean(
                tf.cast(correct_prediction, tf.float32))
    tf.summary.scalar('accuracy', evaluation_step)
    return evaluation_step, prediction


class TrainFromBottlenecks:
    def __init__(self):
        self.sess=None
        self.start_time1 = None
        self.start_time2 = None

    def trainingTesting(self):
        # BASE_FOLDER = os.path.join(os.getenv('RUNTIME_BASEDIR',os.path.abspath(os.path.dirname(__file__))), 'dataset')
        # BOTTLENECKS_FOLDER = os.path.join(os.getenv('RUNTIME_BASEDIR',os.path.abspath(os.path.dirname(__file__))), 'bottlenecks')
        BASE_FOLDER = image_dir_path
        BOTTLENECKS_FOLDER = bottleneck_dir_path
        image_dir = BASE_FOLDER
        bottleneck_dir = BOTTLENECKS_FOLDER

        self.start_time1 = int(time())

        # Look at the folder structure, and create lists of all the images.
        image_lists = create_image_lists(image_dir, testing_percentage,
                                         validation_percentage)
        class_count = len(image_lists.keys())
        if class_count == 0:
            print('No valid folders of images found at ' + image_dir)
        if class_count == 1:
            print('Only one valid folder of images found at ' + image_dir +
                  ' - multiple classes are needed for classification.')

        if class_count < 2:
            return "valid image not enough, multiple classes are needed for classification"

        sess = tf.Session()
        with sess.as_default():
            # Setup the directory we'll write summaries to for TensorBoard
            if tf.gfile.Exists(summaries_dir):
                tf.gfile.DeleteRecursively(summaries_dir)
            tf.gfile.MakeDirs(summaries_dir)
            # Set up the pre-trained graph.
            # We'll make sure we've calculated the 'bottleneck' image summaries and
            # cached them on disk.
            cache_bottlenecks(sess, image_lists, image_dir, bottleneck_dir)
            # Add the new layer that we'll be training.
            (train_step, cross_entropy, bottleneck_input, ground_truth_input,
             final_tensor) = add_final_training_ops(len(image_lists.keys()),
                                                    final_tensor_name)
            # Create the operations we need to evaluate the accuracy of our new layer.
            evaluation_step, prediction = add_evaluation_step(
                final_tensor, ground_truth_input)
            # Merge all the summaries and write them out to /tmp/retrain_logs (by default)
            merged = tf.summary.merge_all()
            train_writer = tf.summary.FileWriter(summaries_dir + '/train',
                                                 sess.graph)
            validation_writer = tf.summary.FileWriter(summaries_dir + '/validation')
            # Set up all our weights to their initial default values.
            init = tf.global_variables_initializer()
            sess.run(init)
            print("TrainFromBottlenecks __init__")

            # Run the training for as many cycles as requested on the command line.
            for i in range(how_many_training_steps):
                # Get a batch of input bottleneck values, either calculated fresh every time
                # with distortions applied, or from the cache stored on disk.
                train_bottlenecks, train_ground_truth, _ = get_random_cached_bottlenecks(
                    sess, image_lists, train_batch_size, 'training',
                    bottleneck_dir, image_dir)
                # Feed the bottlenecks and ground truth into the graph, and run a training
                # step. Capture training summaries for TensorBoard with the `merged` op.
                train_summary, _ = sess.run([merged, train_step],
                                            feed_dict={bottleneck_input: train_bottlenecks,
                                                       ground_truth_input: train_ground_truth})
                train_writer.add_summary(train_summary, i)
                # Every so often, print out how well the graph is training.
                is_last_step = (i + 1 == how_many_training_steps)
                if (i % eval_step_interval) == 0 or is_last_step:
                    train_accuracy, cross_entropy_value = sess.run(
                        [evaluation_step, cross_entropy],
                        feed_dict={bottleneck_input: train_bottlenecks,
                                   ground_truth_input: train_ground_truth})
                    print('%s: Step %d: Train accuracy = %.1f%%' % (datetime.now(), i,
                                                                    train_accuracy * 100))
                    print('%s: Step %d: Cross entropy = %f' % (datetime.now(), i,
                                                               cross_entropy_value))
                    validation_bottlenecks, validation_ground_truth, _ = (
                        get_random_cached_bottlenecks(
                            sess, image_lists, validation_batch_size, 'validation',
                            bottleneck_dir, image_dir))
                    # Run a validation step and capture training summaries for TensorBoard
                    # with the `merged` op.
                    validation_summary, validation_accuracy = sess.run(
                        [merged, evaluation_step],
                        feed_dict={bottleneck_input: validation_bottlenecks,
                                   ground_truth_input: validation_ground_truth})
                    validation_writer.add_summary(validation_summary, i)
                    print('%s: Step %d: Validation accuracy = %.1f%% (N=%d)' %
                          (datetime.now(), i, validation_accuracy * 100,
                           len(validation_bottlenecks)))

            self.start_time2 = int(time())
            # We've completed all our training, so run a final test evaluation on
            # some new images we haven't used before.
            test_bottlenecks, test_ground_truth, test_filenames = (
                get_random_cached_bottlenecks(sess, image_lists, test_batch_size,
                                              'testing', bottleneck_dir,
                                              image_dir))
            test_accuracy, predictions = sess.run(
                [evaluation_step, prediction],
                feed_dict={bottleneck_input: test_bottlenecks,
                           ground_truth_input: test_ground_truth})
            print('Final test accuracy = %.1f%% (N=%d)' % (
                test_accuracy * 100, len(test_bottlenecks)))

            ret_log='Final test accuracy = %.1f%% (N=%d)' % (test_accuracy * 100, len(test_bottlenecks))

            if print_misclassified_test_images:
                print('=== MISCLASSIFIED TEST IMAGES ===')
                for i, test_filename in enumerate(test_filenames):
                    if predictions[i] != test_ground_truth[i].argmax():
                        print('%70s  %s' %
                              (test_filename, image_lists.keys()[predictions[i]]))
            # Write out the trained graph and labels with the weights stored as constants.
            output_graph_def = graph_util.convert_variables_to_constants(
                sess, sess.graph.as_graph_def(), [final_tensor_name])
            with gfile.FastGFile(output_graph_path, 'wb') as f:
                f.write(output_graph_def.SerializeToString())
            with gfile.FastGFile(output_labels_path, 'w') as f:
                f.write('\n'.join(image_lists.keys()) + '\n')

            sess.close()

            return ('Training finised, Total time=%d Final test accuracy = %.1f%% (N=%d)' % (
                   (self.start_time2-self.start_time1), test_accuracy * 100, len(test_bottlenecks)))


def train_from_bottlenecks(image_dir, bottleneck_dir):
    device_id = sys.argv[1]
    group_id = sys.argv[2]
    start_time1 = int(time())
    sess = tf.Session()
    # Setup the directory we'll write summaries to for TensorBoard
    if tf.gfile.Exists(summaries_dir):
        tf.gfile.DeleteRecursively(summaries_dir)
    tf.gfile.MakeDirs(summaries_dir)
    # Set up the pre-trained graph.
    # Look at the folder structure, and create lists of all the images.
    image_lists = create_image_lists(image_dir, testing_percentage,
                                     validation_percentage)
    print(image_lists)
    class_count = len(image_lists.keys())
    if class_count == 0:
        print('No valid folders of images found at ' + image_dir)
    if class_count == 1:
        print('Only one valid folder of images found at ' + image_dir +
              ' - multiple classes are needed for classification.')
    if class_count < 2:
        return "valid image not enough, multiple classes are needed for classification"

    sendMessage2Group(device_id, group_id, "Training now ...")

    start_time = None
    image_counter = 0
    # We'll make sure we've calculated the 'bottleneck' image summaries and
    # cached them on disk.
    cache_bottlenecks(sess, image_lists, image_dir, bottleneck_dir)
    # Add the new layer that we'll be training.
    (train_step, cross_entropy, bottleneck_input, ground_truth_input,
     final_tensor) = add_final_training_ops(len(image_lists.keys()),
                                            final_tensor_name)
    # Create the operations we need to evaluate the accuracy of our new layer.
    evaluation_step, prediction = add_evaluation_step(
        final_tensor, ground_truth_input)
    # Merge all the summaries and write them out to /tmp/retrain_logs (by default)
    merged = tf.summary.merge_all()
    train_writer = tf.summary.FileWriter(summaries_dir + '/train',
                                         sess.graph)
    validation_writer = tf.summary.FileWriter(summaries_dir + '/validation')
    # Set up all our weights to their initial default values.
    init = tf.global_variables_initializer()
    sess.run(init)
    # Run the training for as many cycles as requested on the command line.
    for i in range(how_many_training_steps):
        # Get a batch of input bottleneck values, either calculated fresh every time
        # with distortions applied, or from the cache stored on disk.
        train_bottlenecks, train_ground_truth, _ = get_random_cached_bottlenecks(
            sess, image_lists, train_batch_size, 'training',
            bottleneck_dir, image_dir)
        # Feed the bottlenecks and ground truth into the graph, and run a training
        # step. Capture training summaries for TensorBoard with the `merged` op.
        train_summary, _ = sess.run([merged, train_step],
                                    feed_dict={bottleneck_input: train_bottlenecks,
                                               ground_truth_input: train_ground_truth})
        train_writer.add_summary(train_summary, i)
        # Every so often, print out how well the graph is training.
        is_last_step = (i + 1 == how_many_training_steps)
        if (i % eval_step_interval) == 0 or is_last_step:
            train_accuracy, cross_entropy_value = sess.run(
                [evaluation_step, cross_entropy],
                feed_dict={bottleneck_input: train_bottlenecks,
                           ground_truth_input: train_ground_truth})
            print('%s: Step %d: Train accuracy = %.1f%%' % (datetime.now(), i,
                                                            train_accuracy * 100))
            print('%s: Step %d: Cross entropy = %f' % (datetime.now(), i,
                                                       cross_entropy_value))
            validation_bottlenecks, validation_ground_truth, _ = (
                get_random_cached_bottlenecks(
                    sess, image_lists, validation_batch_size, 'validation',
                    bottleneck_dir, image_dir))
            # Run a validation step and capture training summaries for TensorBoard
            # with the `merged` op.
            validation_summary, validation_accuracy = sess.run(
                [merged, evaluation_step],
                feed_dict={bottleneck_input: validation_bottlenecks,
                           ground_truth_input: validation_ground_truth})
            validation_writer.add_summary(validation_summary, i)
            print('%s: Step %d: Validation accuracy = %.1f%% (N=%d)' %
                  (datetime.now(), i, validation_accuracy * 100,
                   len(validation_bottlenecks)))
    # We've completed all our training, so run a final test evaluation on
    # some new images we haven't used before.
    start_time2 = int(time())
    test_bottlenecks, test_ground_truth, test_filenames = (
        get_random_cached_bottlenecks(sess, image_lists, test_batch_size,
                                      'testing', bottleneck_dir,
                                      image_dir))
    test_accuracy, predictions = sess.run(
        [evaluation_step, prediction],
        feed_dict={bottleneck_input: test_bottlenecks,
                   ground_truth_input: test_ground_truth})
    print('Final test accuracy = %.1f%% (N=%d)' % (
        test_accuracy * 100, len(test_bottlenecks)))
    if print_misclassified_test_images:
        print('=== MISCLASSIFIED TEST IMAGES ===')
        for i, test_filename in enumerate(test_filenames):
            if predictions[i] != test_ground_truth[i].argmax():
                print('%70s  %s' %
                      (test_filename, image_lists.keys()[predictions[i]]))
    # Write out the trained graph and labels with the weights stored as constants.
    output_graph_def = graph_util.convert_variables_to_constants(
        sess, sess.graph.as_graph_def(), [final_tensor_name])
    with gfile.FastGFile(output_graph_path, 'wb') as f:
        f.write(output_graph_def.SerializeToString())
    with gfile.FastGFile(output_labels_path, 'w') as f:
        f.write('\n'.join(image_lists.keys()) + '\n')
    log =  ('Training finised, Total time=%d Final test accuracy = %.1f%% (N=%d)' % (
        (start_time2 - start_time1), test_accuracy * 100, len(test_bottlenecks)))
    sendMessage2Group(device_id, group_id, log)


if __name__ == '__main__':
    groupid = sys.argv[2]
    group_path = os.path.join(BASEPATH, groupid)
    image_dir_path = os.path.join(group_path, 'dataset')
    bottleneck_dir_path = os.path.join(group_path, "bottlenecks")
    output_graph_path = os.path.join(group_path, output_graph)
    output_labels_path = os.path.join(group_path, output_labels)

    if not os.path.exists(group_path):
        os.mkdir(group_path)
        os.mkdir(image_dir_path)
        os.mkdir(bottleneck_dir_path)
    train_from_bottlenecks(image_dir=image_dir_path, bottleneck_dir=bottleneck_dir_path)
