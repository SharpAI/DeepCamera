# coding=utf-8
import os, time
import heapq

BASEPATH = os.path.abspath(os.getenv('RUNTIME_BASEDIR',os.path.dirname(__file__)))
# pb_path = 'faces/embedding_graph.pb'
# label_txt_path = "faces/output_labels.txt"
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

    return None

def load_graph_sess(frozen_graph_filename):
    return None, None


def init_graph(pb_file):
    global sess_def
    global graph_def

    if sess_def is not None:
        with graph_def.as_default():
            with sess_def.as_default():
                sess_def.close()

    sess_def, graph_def = load_graph_sess(pb_file)


def test_on_bottleneck(bottleneck_file, groupid, img_style):
    global last_modify_time
    group_path = os.path.join(BASEPATH, groupid, img_style)
    pb_path = os.path.join(group_path,'embedding_graph.pb')
    stat_info = os.stat(pb_path)
    modify_time = stat_info.st_mtime
    if modify_time != last_modify_time:  # if pb was modified
        last_modify_time = modify_time
        init_graph(pb_path)
        print("pb was modified".center(40, '*'))
    return predict(bottleneck_file, group_path)

#
# if __name__ == '__main__':
#     test_on_bottleneck(bottleneck_file=bottleneck_file, groupid)
