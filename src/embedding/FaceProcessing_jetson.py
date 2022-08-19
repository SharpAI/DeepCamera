from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import base64
from StringIO import StringIO
from PIL import Image
import numpy as np
import cv2
import os
import time

from scipy import misc
from scipy.misc import imread, imresize
import torch
from torchvision import transforms
import time
import insightface

DATA_RUNTIME_FOLDER = os.getenv('DATA_RUNTIME_FOLDER', '/data/runtime')
HAS_OPENCL = os.getenv('HAS_OPENCL', 'false')

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
preprocess = None
embedder = None
device = None
def init_embedding_processor():
    global embedder
    global preprocess
    global device

    embedder = insightface.iresnet34(pretrained=True).cuda()
    embedder.eval()

    mean = [0.5] * 3
    std = [0.5 * 256 / 255] * 3
    preprocess = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize(mean, std)
    ])
    use_cuda = torch.cuda.is_available()
    device = torch.device("cuda" if use_cuda else "cpu")

    return embedder

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
    global embedder
    global preprocess
    global device

    nimg = np.transpose(img, (2,0,1))
    resize_img = misc.imresize(nimg, [112, 112], interp='bilinear')
    tensor = preprocess(resize_img)
    with torch.no_grad():
        features = embedder(tensor.unsqueeze(0).to(device))[0]
        features = features.to(torch.device('cpu')).numpy().flatten() #.detach().numpy().flatten()

        print(features[:32])
        return features
    return None
