# coding=utf-8
import os, time
#import sys
import heapq
import tensorflow as tf

BASEPATH = os.path.abspath(os.getenv('RUNTIME_BASEDIR',os.path.dirname(__file__)))
# pb_path = 'bottlenecks_graph.pb'
bottleneck_file = 'test_images/2af60667790f86b7c23df4967YRBBDB722205800149309903838612.jpg.txt'
sess_def=None
graph_def=None
modify_time = None
last_modify_time = None


def get_bottleneck(bottleneck_file):
    with open(bottleneck_file, 'r') as bottleneck_file:
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


def load_graph(frozen_graph_filename):
    with tf.gfile.GFile(frozen_graph_filename, "rb") as f:
        graph_def = tf.GraphDef()
        graph_def.ParseFromString(f.read())

    with tf.Graph().as_default() as graph:
        _ = tf.import_graph_def(graph_def, name='')

    return graph


def load_graph_sess(frozen_graph_filename):
    graph = load_graph(frozen_graph_filename)
    with tf.Session(graph=graph) as sess:
        #sess.run(tf.global_variables_initializer())
        return sess, graph


def init_graph(pb_file):
    global sess_def
    global graph_def

    if sess_def is not None:
        with graph_def.as_default():
            with sess_def.as_default():
                sess_def.close()

    sess_def, graph_def = load_graph_sess(pb_file)


def predict(bottleneck_file, groupid):
    ts1 = int(time.time()*1000)
    test_bottleneck = get_bottleneck(bottleneck_file)
    if test_bottleneck is None:
        print('Load bottle file error, exiting')
        os._exit(0)

    with graph_def.as_default():
        with sess_def.as_default():
            softmax_tensor = sess_def.graph.get_tensor_by_name('final_result:0')
            predictions = sess_def.run(softmax_tensor, {'input/BottleneckInputPlaceholder:0': [test_bottleneck]})
    ts2 = int(time.time()*1000)
    print predictions
    print ("time= %d ms " %(ts2-ts1))

    # Sort to show labels of first prediction in order of confidence
    top_k = predictions[0].argsort()[-len(predictions[0]):][::-1]

    score_human_string = []
    group_path = os.path.join(BASEPATH, groupid)
    label_txt_path = os.path.join(group_path, 'output_labels.txt')
    label_lines = [line.rstrip() for line
                   in tf.gfile.GFile(label_txt_path)]
    for node_id in top_k:
        human_string = label_lines[node_id]
        score = predictions[0][node_id]
        print('%s (score = %.5f)' % (human_string, score))
        score_human_string.append((score, human_string))
    number1, number2 = heapq.nlargest(2, score_human_string, key=lambda x: x[0])  # 得分前两类
    fraction = number1[0] / (number1[0] + number2[0])
    print(fraction)
    return number1[0], number1[1], fraction


def test_on_bottleneck(bottleneck_file, groupid):
    global last_modify_time
    group_path = os.path.join(BASEPATH, groupid)
    pb_path = os.path.join(group_path, 'bottlenecks_graph.pb')
    stat_info = os.stat(pb_path)
    modify_time = stat_info.st_mtime
    if modify_time != last_modify_time:  # if pb was modified
        last_modify_time = modify_time
        init_graph(pb_path)
        print("pb was modified".center(40, '*'))
    return predict(bottleneck_file, groupid)


# if __name__ == '__main__':
#     test_on_bottleneck(bottleneck_file=bottleneck_file)
