"""ssd_tf.py

This module implements the TfSSD class.
"""


import numpy as np
import cv2
import tensorflow as tf


def _postprocess_tf(img, boxes, scores, classes, conf_th):
    """Postprocess TensorFlow SSD output."""
    h, w, _ = img.shape
    out_boxes = boxes[0] * np.array([h, w, h, w])
    out_boxes = out_boxes.astype(np.int32)
    out_boxes = out_boxes[:, [1, 0, 3, 2]]  # swap x's and y's
    out_confs = scores[0]
    out_clss = classes[0].astype(np.int32)

    # only return bboxes with confidence score above threshold
    mask = np.where(out_confs >= conf_th)
    return out_boxes[mask], out_confs[mask], out_clss[mask]


class TfSSD(object):
    """TfSSD class encapsulates things needed to run TensorFlow SSD."""

    def __init__(self, model, input_shape):
        self.model = model
        self.input_shape = input_shape

        # load detection graph
        ssd_graph = tf.Graph()
        with ssd_graph.as_default():
            graph_def = tf.GraphDef()
            with tf.gfile.GFile('ssd/%s.pb' % model, 'rb') as fid:
                serialized_graph = fid.read()
                graph_def.ParseFromString(serialized_graph)
                tf.import_graph_def(graph_def, name='')

        # define input/output tensors
        self.image_tensor = ssd_graph.get_tensor_by_name('image_tensor:0')
        self.det_boxes = ssd_graph.get_tensor_by_name('detection_boxes:0')
        self.det_scores = ssd_graph.get_tensor_by_name('detection_scores:0')
        self.det_classes = ssd_graph.get_tensor_by_name('detection_classes:0')

        # create the session for inferencing
        self.sess = tf.Session(graph=ssd_graph)

    def __del__(self):
        self.sess.close()

    def detect(self, img, conf_th):
        img_resized = _preprocess_tf(img, self.input_shape)
        boxes, scores, classes = self.sess.run(
            [self.det_boxes, self.det_scores, self.det_classes],
            feed_dict={self.image_tensor: np.expand_dims(img_resized, 0)})
        return _postprocess_tf(img, boxes, scores, classes, conf_th)
