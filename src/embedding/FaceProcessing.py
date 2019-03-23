from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import base64
from StringIO import StringIO
from PIL import Image
import numpy as np
import argparse
import facenet
import align.detect_face
import cv2
import os
import sys
import time
import math

from scipy import misc
from sklearn import metrics
from scipy.optimize import brentq
from scipy import interpolate
from scipy.misc import imread, imresize
import sklearn.preprocessing

global mx
mx = None
global globGraph
globGraph = None
global mod
global mod2
mod2 = None
global mod3
mod3 = None
DEBUG = False

DATA_RUNTIME_FOLDER = os.getenv('DATA_RUNTIME_FOLDER', '/data/runtime')
HAS_OPENCL = os.getenv('HAS_OPENCL', 'true')

def load_graph(frozen_graph_filename):
    return None

def crop(image, random_crop, image_size):
    if image.shape[1]>image_size:
        sz1 = int(image.shape[1]//2)
        sz2 = int(image_size//2)
        if random_crop:
            diff = sz1-sz2
            (h, v) = (np.random.randint(-diff, diff+1), np.random.randint(-diff, diff+1))
        else:
            (h, v) = (0,0)
        image = image[(sz1-sz2+v):(sz1+sz2+v),(sz1-sz2+h):(sz1+sz2+h),:]
    return image

def flip(image, random_flip):
    if random_flip and np.random.choice([True, False]):
        image = np.fliplr(image)
    return image

def to_rgb(img):
    w, h = img.shape
    ret = np.empty((w, h, 3), dtype=np.uint8)
    ret[:, :, 0] = ret[:, :, 1] = ret[:, :, 2] = img
    return ret

def load_image(image_path):

    img_list = [None] * 1
    img = misc.imread(os.path.expanduser(image_path))
    img_size = np.asarray(img.shape)[0:2]
    prewhitened = facenet.prewhiten(img)
    img_list[0] = prewhitened
    image = np.stack(img_list)
    return image

def init_FaceProcessing(model_path):
    global globGraph

    if globGraph != None:
        return globGraph

    globGraph = load_graph(model_path)

    previous = 'no'
    for op in globGraph.get_operations():
        try:
            firstLevel = op.name.split("/")[1]
            if firstLevel.startswith(previous) is not True:
                print(op.name)
                previous = firstLevel
        except:
            print(op.name)

    return globGraph

def InitialFaceProcessor(model_path):
    return None , None
def get_model(ctx, image_size, model_str, layer):
  _vec = model_str.split(',')
  assert len(_vec)==2
  prefix = _vec[0]
  epoch = int(_vec[1])
  print('loading',prefix, epoch)
  sym, arg_params, aux_params = mx.model.load_checkpoint(prefix, epoch)
  all_layers = sym.get_internals()
  sym = all_layers[layer+'_output']
  model = mx.mod.Module(symbol=sym, context=ctx, label_names = None)
  #model.bind(data_shapes=[('data', (args.batch_size, 3, image_size[0], image_size[1]))], label_shapes=[('softmax_label', (args.batch_size,))])
  model.bind(data_shapes=[('data', (1, 3, 112, 112))])
  model.set_params(arg_params, aux_params)
  return model
def init_embedding_processor():
    global mod2
    global mod3

    if HAS_OPENCL == 'false':
        global mx
        import mxnet as mx
        print('need init mxnet')

        mod2 = None
        if os.path.isfile(DATA_RUNTIME_FOLDER+'/model-0000.params'):
            ctx = mx.cpu(0)
            mod3 = get_model(ctx, [112,112], DATA_RUNTIME_FOLDER+'/model,0', 'fc1')
            print('backup model loaded')
            return mod3
    else:
        print('has opencl supporting')

    if os.path.isfile(DATA_RUNTIME_FOLDER+'/net2'):
        global __t
        global graph_runtime
        try:
            import tvm as __t
            from tvm.contrib import graph_runtime
            loaded_lib = None
            if os.path.isfile(DATA_RUNTIME_FOLDER+'/net2.tar.so'):
                loaded_lib = __t.module.load(DATA_RUNTIME_FOLDER+'/net2.tar.so')
            else:
                loaded_lib = __t.module.load(DATA_RUNTIME_FOLDER+'/net2.tar')
            loaded_json = open(DATA_RUNTIME_FOLDER+"/net2").read()
            loaded_params = bytearray(open(DATA_RUNTIME_FOLDER+"/net2.params", "rb").read())

            ctx = __t.cl(0)

            mod2 = graph_runtime.create(loaded_json, loaded_lib, ctx)
            mod2.load_params(loaded_params)
            return mod2
        except:
            print('error of loading net2')
            mod2 = None
            if os.path.isfile(DATA_RUNTIME_FOLDER+'/model-0000.params'):
                global mx
                import mxnet as mx
                ctx = mx.cpu(0)
                mod3 = get_model(ctx, [112,112], DATA_RUNTIME_FOLDER+'/model,0', 'fc1')
                print('backup model loaded')
                return mod3
    elif os.path.isfile('/root/model-r50-am-lfw/model-0000.params'):
        global mx
        import mxnet as mx
        ctx = mx.cpu(0)
        mod3 = get_model(ctx, [112,112], '/root/model-r50-am-lfw/model,0', 'fc1')
        print('backup model loaded')
        return mod3

def FaceProcessingOne(imgpath,sess,graph):
    images_placeholder = graph.get_tensor_by_name("import/input:0")
    embeddings = graph.get_tensor_by_name("import/embeddings:0")
    phase_train_placeholder = graph.get_tensor_by_name("import/phase_train:0")

    image_size = 160 #images_placeholder.get_shape()[1]
    embedding_size = 128 #embeddings.get_shape()[1]
    # Run forward pass to calculate embeddings
    print('Runnning forward pass on LFW images')
    batch_size = 1 #args.lfw_batch_size
    nrof_batches = 1

    image = load_image(imgpath)

    feed_dict = { images_placeholder:image, phase_train_placeholder:False }
    features = sess.run(embeddings, feed_dict=feed_dict)

    return features

def FaceProcessingImageData(imgData,sess,graph):
    images_placeholder = graph.get_tensor_by_name("import/input:0")
    embeddings = graph.get_tensor_by_name("import/embeddings:0")
    phase_train_placeholder = graph.get_tensor_by_name("import/phase_train:0")

    image_size = 160 #images_placeholder.get_shape()[1]
    embedding_size = 128 #embeddings.get_shape()[1]
    # Run forward pass to calculate embeddings
    print('Runnning forward pass on LFW images')
    batch_size = 1 #args.lfw_batch_size
    nrof_batches = 1

    img_list = [None] * 1
    img_list[0] = imgData
    image = np.stack(img_list)

    feed_dict = { images_placeholder:image, phase_train_placeholder:False }
    features = sess.run(embeddings, feed_dict=feed_dict)

    return features

def FaceProcessingImageData2(img_path):
    img_data = misc.imread(img_path)
    img = cv2.cvtColor(img_data, cv2.COLOR_BGR2RGB)
    return _FaceProcessingImageData2(img)

def FaceProcessingBase64ImageData2(base64_string):
    sbuf = StringIO()
    sbuf.write(base64.b64decode(base64_string))
    pimg = Image.open(sbuf)
    img = np.array(pimg)
    #img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    return _FaceProcessingImageData2(img)

def _FaceProcessingImageData2(img):
    global mod2
    global mod3

    embedding = None

    nimg = np.transpose(img, (2,0,1))
    resize_img = misc.imresize(nimg, [112, 112], interp='bilinear')
    if mod2 is not None:
        a = transform_image(resize_img).astype('float32')
        mod2.run(data=a)
        try:
            out1 = mod2.get_output(0).asnumpy()
        except TypeError as err:
            out1 = mod2.get_output(0, __t.nd.empty((512,))).asnumpy()
        embedding = sklearn.preprocessing.normalize(out1).flatten()
    elif mod3 is not None:
        aligned = resize_img.transpose((2, 0, 1))
        input_blob = np.expand_dims(aligned, axis=0)
        data = mx.nd.array(input_blob)
        db = mx.io.DataBatch(data=(data,))
        mod3.forward(db, is_train=False)
        embedding = mod3.get_outputs()[0].asnumpy()
        embedding = sklearn.preprocessing.normalize(embedding).flatten()
    return embedding

def transform_image(image):
    #image = np.array(image) - np.array([123., 117., 104.])
    #image /= np.array([58.395, 57.12, 57.375])
    image = image.transpose((2, 0, 1))
    image = image[np.newaxis, :]
    return image
