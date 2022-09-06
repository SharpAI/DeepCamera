import os
import sys
import json
import time
import cv2
import tensorflow as tf
import numpy as np

from upload_img import qiniu_upload_img as q_upload
print sys.path

from utils import label_map_util
from utils import visualization_utils as vis_util
from celery import Celery
from celery import Task
from billiard import current_process
from celery.signals import worker_process_init
from celery.signals import celeryd_after_setup
from celery.concurrency import asynpool
import matplotlib.pyplot as plt

MIN_SCORE_THRESH = 0.60
VIS_ENABLE = False
DRAW_ENABLE = False

detection_graph = None
sess = None
detection_boxes = None
detection_scores = None
detection_classes = None
num_detections = None
detection_masks = None
image_tensor = None
category_index = None
hog = None

asynpool.PROC_ALIVE_TIMEOUT = 120.0 #set this long enough


od = Celery('od',
    broker='redis://guest@redis/0',
    backend='redis://guest@redis/0'
)

@worker_process_init.connect()
def setup(sender=None, **kwargs):
    global detection_graph
    global sess
    global detection_boxes
    global detection_scores
    global detection_classes
#    global detection_masks
    global num_detections
    global image_tensor
    global hog
    global category_index

    NUM_CLASSES = 90
    MODEL_NAME = 'ssdlite_mobilenet_v2_coco_2018_05_09'
    # Path to frozen detection graph. This is the actual model that is used for the object detection.
    PATH_TO_CKPT = MODEL_NAME + '/frozen_inference_graph.pb'
    # List of the strings that is used to add correct label for each box.
    PATH_TO_LABELS = os.path.join(MODEL_NAME, 'mscoco_label_map.pbtxt')
    label_map = label_map_util.load_labelmap(PATH_TO_LABELS)
    categories = label_map_util.convert_label_map_to_categories(label_map, max_num_classes=NUM_CLASSES, use_display_name=True)
    category_index = label_map_util.create_category_index(categories)

    print('init object detect')

    detection_graph = tf.Graph()
    with detection_graph.as_default():
    	od_graph_def = tf.GraphDef()
        with tf.gfile.GFile(PATH_TO_CKPT, 'rb') as fid:
            serialized_graph = fid.read()
            od_graph_def.ParseFromString(serialized_graph)
            tf.import_graph_def(od_graph_def, name='')

    sess = tf.Session(graph=detection_graph)
#    with detection_graph.as_default():    
#        with tf.Session() as sess:
#            ops = tf.get_default_graph().get_operations()
#            all_tensor_names = {output.name for op in ops for output in op.outputs}
#            print('ALL TENSORS: ',all_tensor_names)
    # Input tensor is the image
    image_tensor = detection_graph.get_tensor_by_name('image_tensor:0')

    # Output tensors are the detection boxes, scores, and classes
    # Each box represents a part of the image where a particular object was detected
    detection_boxes = detection_graph.get_tensor_by_name('detection_boxes:0')

    # Each score represents level of confidence for each of the objects.
    # The score is shown on the result image, together with the class label.
    detection_scores = detection_graph.get_tensor_by_name('detection_scores:0')
    detection_classes = detection_graph.get_tensor_by_name('detection_classes:0')
    
    
    # Number of objects detected
    num_detections = detection_graph.get_tensor_by_name('num_detections:0')
#    detection_masks = detection_graph.get_tensor_by_name('detection_masks:0')

    #print('init people detect')
    #hog = cv2.HOGDescriptor()
    #hog.setSVMDetector( cv2.HOGDescriptor_getDefaultPeopleDetector() )

    return "detection"
@od.task
def people_detect(image_path, trackerid, ts, cameraId):
    global hog
    #image = cv2.imread(image_path)

    #found,w=hog.detectMultiScale(image, winStride=(8,8), padding=(32,32), scale=1.05)

    #return found
    return 'ok'
@od.task
def detect(image_path, trackerid, ts, cameraId):
    global sess
    global detection_graph
    global detection_boxes
    global detection_scores
    global detection_classes
    global num_detections
#    global detection_masks
    global image_tensor
    global category_index
    global MIN_SCORE_THRESH
    url = None    
    print('start detection.... reading image...')
    image = cv2.imread(image_path)
   
    image_expanded = np.expand_dims(image, axis=0)
    # Perform the actual detection by running the model with the image as input
   
    (boxes, scores, classes, num) = sess.run(
    [detection_boxes, detection_scores, detection_classes, num_detections],
    feed_dict={image_tensor: image_expanded})
    detected = False
    results = []

    # Draw boxes without labels
    if DRAW_ENABLE is True:
        with detection_graph.as_default():
            image_raw = tf.gfile.FastGFile(image_path).read()
            image_data = tf.image.decode_jpeg(image_raw)
            image_data = tf.expand_dims(tf.image.convert_image_dtype(image_data,tf.float32),0)
            result = tf.image.draw_bounding_boxes(image_data,boxes)
            result_shape = sess.run(result).shape

            result = result.eval(session=sess).reshape([result_shape[1],result_shape[2],result_shape[3]])
            plt.imsave(str(trackerid)+'_box.jpg',result)

    boxes = np.squeeze(boxes)
    classes = np.squeeze(classes).astype(np.int32)
    scores = np.squeeze(scores)
    # Draw boxes with labels,currently only showing main box
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    if VIS_ENABLE is True:    
        if any(boxes[0]) is True:
            image_vis = vis_util.visualize_boxes_and_labels_on_image_array(
    	        image,
                boxes[0,:].reshape(1,4),
                classes,
                scores,
                category_index,
                use_normalized_coordinates=True,
                line_thickness=5
            )
            img_path = str(trackerid)+'_box'
            plt.imsave(img_path,image_vis)  
            url = q_upload(str(trackerid),img_path+'.png' ,30)

    for i in range(boxes.shape[0]):
        if scores is not None and scores[i] > MIN_SCORE_THRESH:
            detected = True
            if classes[i] in category_index.keys():
              class_name = category_index[classes[i]]['name']
            else:
              class_name = 'N/A'
            display_str = str(class_name)
            json_record = {'acc':str(scores[i]),
                'name':display_str,'box':str(boxes[i])}
            results.append(json_record)

    print(results)
    if len(results) == 0:
        return json.dumps({'detected': None})
    else: 
        return json.dumps({'detected':detected,'results':results, 'url':url})

if __name__ == '__main__':
    od.start()
