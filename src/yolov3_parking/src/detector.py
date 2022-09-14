from __future__ import division
import os
import json
import threading
import queue
import time
import argparse
import random 

from flask import Flask
from flask import request
from flask import jsonify
import torch 
import torch.nn as nn
from torch.autograd import Variable
import numpy as np
import cv2 
from util import *
from darknet import Darknet
from preprocess import prep_image, inp_to_image, letterbox_image
import pandas as pd
import pickle as pkl

app = Flask(__name__)
q = queue.Queue(1)
classes = load_classes('data/coco.names')
colors = pkl.load(open("pallete", "rb"))

def get_test_input(input_dim, CUDA):
    img = cv2.imread("Khare_frame_02.png")
    img = cv2.resize(img, (input_dim, input_dim)) 
    img_ =  img[:,:,::-1].transpose((2,0,1))
    img_ = img_[np.newaxis,:,:,:]/255.0
    img_ = torch.from_numpy(img_).float()
    img_ = Variable(img_)
    
    if CUDA:
        img_ = img_.cuda()
    
    return img_

def prep_image(img, inp_dim):
    """
    Prepare image for inputting to the neural network. 
    
    Returns a Variable 
    """
    orig_im = img
    dim = orig_im.shape[1], orig_im.shape[0]
    img = (letterbox_image(orig_im, (inp_dim, inp_dim)))
    img_ = img[:,:,::-1].transpose((2,0,1)).copy()
    img_ = torch.from_numpy(img_).float().div(255.0).unsqueeze(0)
    return img_, orig_im, dim

def write(x, img):
    c1 = tuple(x[1:3].int())
    c2 = tuple(x[3:5].int())
    cls = int(x[-1])
    label = "{0}".format(classes[cls])
    color = (0,0,255)
    cv2.rectangle(img, c1, c2,color, 1)
    t_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_PLAIN, 1 , 1)[0]
    c2 = c1[0] + t_size[0] + 3, c1[1] + t_size[1] + 4
    cv2.rectangle(img, c1, c2,color, -1)
    cv2.putText(img, label, (c1[0], c1[1] + t_size[1] + 4), cv2.FONT_HERSHEY_PLAIN, 1, [225,255,255], 1);
    return img

def arg_parse():
    """
    Parse arguements to the detect module
    """
    parser = argparse.ArgumentParser(description='YOLO v3 Video Detection Module')
    parser.add_argument("--video", dest = 'video', help = 
                        "Video to run detection upon",
                        default = "video.avi", type = str)
    parser.add_argument("--dataset", dest = "dataset", help = "Dataset on which the network has been trained", default = "pascal")
    parser.add_argument("--confidence", dest = "confidence", help = "Object Confidence to filter predictions", default = 0.5)
    parser.add_argument("--nms_thresh", dest = "nms_thresh", help = "NMS Threshhold", default = 0.4)
    parser.add_argument("--cfg", dest = 'cfgfile', help = 
                        "Config file",
                        default = "cfg/yolov3.cfg", type = str)
    parser.add_argument("--weights", dest = 'weightsfile', help = 
                        "weightsfile",
                        default = "yolov3.weights", type = str)
    parser.add_argument("--reso", dest = 'reso', help = 
                        "Input resolution of the network. Increase to increase accuracy. Decrease to increase speed",
                        default = "800", type = str)
    return parser.parse_args()

@app.route('/submit/image', methods=['POST'])
def submit_image():
    json_data = json.loads(request.data)
    camera_id = json_data['args'][0]
    filename = json_data['args'][1]
    print(f'filename: {filename}, camera_id: {camera_id}')

    try:
        q.put_nowait(filename)
        return 'processing', 200
    except:
        os.remove(filename)
        return 'skip frame', 200

def worker():
    args = arg_parse()
    confidence = float(args.confidence)
    nms_thesh = float(args.nms_thresh)
    start = 0
    CUDA = torch.cuda.is_available()
    num_classes = 1
    CUDA = torch.cuda.is_available()
    bbox_attrs = 5 + num_classes
    print("Loading network.....")
    model = Darknet(args.cfgfile)
    model.load_weights(args.weightsfile)
    print("Network successfully loaded")
    model.net_info["height"] = args.reso
    inp_dim = int(model.net_info["height"])
    if CUDA:
        model.cuda()
        
    model(get_test_input(inp_dim, CUDA), CUDA)
    model.eval()
    
    frames = 0
    start = time.time()

    while True:        
        item = q.get()
        print(f'Working on {item}')
        img = cv2.imread(item)
        frame = cv2.resize(img, (800,600), interpolation = cv2.INTER_AREA)

        img, orig_im, dim = prep_image(frame, inp_dim)
        im_dim = torch.FloatTensor(dim).repeat(1,2)                        

        if CUDA:
            im_dim = im_dim.cuda()
            img = img.cuda()
        
        with torch.no_grad():   
            output = model(Variable(img), CUDA)
        output = write_results(output, confidence, num_classes, nms = True, nms_conf = nms_thesh)
        print("count cars {}".format(output.size(0)))
        
        if type(output) == int:
            frames += 1
            print("FPS of the video is {:5.2f}".format( frames / (time.time() - start)))
            cv2.imshow("frame", orig_im)
            key = cv2.waitKey(1)
            if key & 0xFF == ord('q'):
                break
            continue

        im_dim = im_dim.repeat(output.size(0), 1)
        scaling_factor = torch.min(inp_dim/im_dim,1)[0].view(-1,1)
        
        output[:,[1,3]] -= (inp_dim - scaling_factor*im_dim[:,0].view(-1,1))/2
        output[:,[2,4]] -= (inp_dim - scaling_factor*im_dim[:,1].view(-1,1))/2
        
        output[:,1:5] /= scaling_factor

        for i in range(output.shape[0]):
            output[i, [1,3]] = torch.clamp(output[i, [1,3]], 0.0, im_dim[i,0])
            output[i, [2,4]] = torch.clamp(output[i, [2,4]], 0.0, im_dim[i,1])
        
        list(map(lambda x: write(x, orig_im), output))
        empty = 60 - output.size(0)
        cv2.putText(orig_im, "Total empty spots: " + str(empty), (5,30), cv2.FONT_HERSHEY_PLAIN, 1, [0,0,0], 2, cv2.LINE_AA)
        
        cv2.imshow("Parking 1", orig_im)
        key = cv2.waitKey(1)
        if key & 0xFF == ord('q'):
            break
        frames += 1
        print("FPS of the video is {:5.2f}".format( frames / (time.time() - start)))
        
    
        print(f'Finished {item}')
        q.task_done()
    

# Turn-on the worker thread.
threading.Thread(target=worker, daemon=True).start()

app.run(host='0.0.0.0', port=3000)
