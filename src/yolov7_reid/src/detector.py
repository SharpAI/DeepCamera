import os
import time
import queue
import json
import argparse
import threading
import time
import pafy
from pymilvus import (connections, CollectionSchema, 
                      FieldSchema, DataType, Collection, utility)
import redis
import numpy as np
import cv2
import onnxruntime

from flask import Flask
from flask import request
from flask import jsonify
from YOLOv7 import YOLOv7
from LabelStudioClient import LabelStudioClient
from telegram_bot import TelegramBot

model_path = "models/yolov7-tiny_480x640.onnx"
yolov7_detector = YOLOv7(model_path, conf_thres=0.6, iou_thres=0.5)

app = Flask(__name__)
q = queue.Queue(1)
def get_parser():
    parser = argparse.ArgumentParser(description="onnx model inference")

    parser.add_argument(
        "--model-path",
        default="./models/mgn_R50-ibn.onnx",
        help="onnx model path"
    )
    parser.add_argument(
        "--height",
        type=int,
        default=384,
        help="height of image"
    )
    parser.add_argument(
        "--width",
        type=int,
        default=128,
        help="width of image"
    )
    return parser

def init_milvus(collection_name, dim):
    connections.connect(host="milvus", port=19530)
    red = redis.Redis(host='redis', port=6379, db=0)
    red.flushdb()

    default_fields = [
        FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
        FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=dim)
    ]
    default_schema = CollectionSchema(fields=default_fields, description="Image test collection")
    
    collection_name = collection_name + f'_dim_{dim}'
    collection = Collection(name=collection_name, schema=default_schema)

    if not utility.has_collection(collection_name):
        default_index = {"index_type": "IVF_SQ8", "params": {"nlist": 512}, "metric_type": "L2"}
        collection.create_index(field_name="vector", index_params=default_index)
    collection.load()
    
    return collection, red
def preprocess(original_image, image_height, image_width):
    # the model expects RGB inputs
    original_image = original_image[:, :, ::-1]

    # Apply pre-processing to image.
    img = cv2.resize(original_image, (image_width, image_height), interpolation=cv2.INTER_CUBIC)
    img = img.astype("float32").transpose(2, 0, 1)[np.newaxis]  # (1, 3, h, w)
    return img
def normalize(nparray, order=2, axis=-1):
    """Normalize a N-D numpy array along the specified axis."""
    norm = np.linalg.norm(nparray, ord=order, axis=axis, keepdims=True)
    return nparray / (norm + np.finfo(np.float32).eps)

q = queue.Queue(1)
args = get_parser().parse_args()
ort_sess = onnxruntime.InferenceSession(args.model_path)
input_name = ort_sess.get_inputs()[0].name

while True:
    try:
        collection, red = init_milvus('yolov7_reid',2048)
        break
    except Exception as e:
        print('waiting for milvus start')
        time.sleep(5)


telegram_bot = TelegramBot()
previous_known_person_ts = 0

def insert_to_milvus(vec, min_dist):
    ids = []
    search_param = {
    "data": [vec],
    "anns_field": 'vector',
    "param": {"metric_type": 'L2', "params": {"nprobe": 16}},
    "limit": 3}

    insert = True
    results = collection.search(**search_param)
    for i, result in enumerate(results):
        print("\nSearch result for {}th vector: ".format(i))
        for j, res in enumerate(result):
            print("Top {}: {}".format(j, res))
            
            if res.distance < min_dist:
                insert = False
                ids.append(res.id)
                break
    if insert == True:
        print('found new feature, insert to vector database')
        mr = collection.insert([[vec]])
        ids = mr.primary_keys
    return insert, ids

def detection_with_image(frame):
    global previous_known_person_ts
    # cv2.imshow('Screen',img)
    # Detect Objects
    KNOWN_COLOR = (0,255,0)
    UNKNOWN_COLOR = (0,0,255)
    bboxes, scores, class_ids = yolov7_detector(frame)
    cropped_imgs, person_bboxes, person_scores, person_class_ids = yolov7_detector.crop_class(frame, bboxes, scores, class_ids, 'person', 100)
    
    pre_colors = []
    unknown = 0
    total = len(cropped_imgs)
    if total > 0:
        for img in cropped_imgs:
            try:
                image = preprocess(img, args.height, args.width)
            except Exception as e:
                print('cant preprocess img')
                print(e)
                continue
            feat = ort_sess.run(None, {input_name: image})[0]
            feat = normalize(feat, axis=1)

            insert,ids = insert_to_milvus(feat[0],0.1)
            if insert is True:
                pre_colors.append(UNKNOWN_COLOR)
                print('inserted') 
                print(feat.shape)
                print(feat[0])
                unknown +=1
                id = ids[0]
                
                filepath = f'/tmp/{id}.png'
                cv2.imwrite(filepath,img)
                
                LabelStudioClient.create_task_with_file(filepath)
                os.remove(filepath)
            else:
                pre_colors.append(KNOWN_COLOR)
        if unknown > 0:
            if unknown == 1:
                telegram_bot.send('SharpAI seen one unknown person')
            else:
                telegram_bot.send(f'SharpAI seen {unknown} unknown people')
        elif total > 0:
            print(f'SharpAI seen {total} person')
            current_ts = time.time()
            if current_ts - previous_known_person_ts > 30*60:
                previous_known_person_ts = current_ts
                telegram_bot.send(f'SharpAI seen {total} person')

        combined_img = yolov7_detector.draw_detections_with_predefined_colors(frame,person_bboxes, person_scores, person_class_ids,pre_colors)
        
        try:
            q.put_nowait(combined_img)
        except queue.Full:
            print('display queue full')

    ret_json = {'total':len(cropped_imgs),'unknown':unknown}
    return ret_json

# telegram_bot.start()

def worker():    
    while True:
        item = q.get()
        print(f'Working on {item}')
        
        try:
            cv2.namedWindow("Detection result", cv2.WINDOW_NORMAL)
            # cv2.setWindowProperty("Screen", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
            cv2.imshow("Detection result", item)

            if cv2.waitKey(25) & 0xFF == ord('q'):
                cv2.destroyAllWindows()
        except Exception as e:
            print('exception:')
            print(e)
            continue

        q.task_done()
        # os.remove(item)

@app.route('/submit/image', methods=['POST'])
def submit_image():
    json_data = json.loads(request.data)

    camera_id = json_data['camera_id']
    filename = json_data['filename']
    print(f'filename: {filename}, camera_id: {camera_id}')

    img = cv2.imread(filename,cv2.IMREAD_ANYCOLOR)

    # Draw detections
    ret = detection_with_image(img)

    os.remove(filename)
    return jsonify(ret)

@app.route('/submit/video_url', methods=['POST'])
def submit_video_url():
    json_data = json.loads(request.data)

    video_url = json_data['video_url']
    print(f'video_url: {video_url}')

    video_task=threading.Thread(target=video_worker,args=(video_url,))
    video_task.start()

    return 'ok', 200

def video_worker(video_url):
    videoPafy = pafy.new(video_url)
    print(videoPafy.streams)
    cap = cv2.VideoCapture(videoPafy.streams[-1].url)
    start_time = 0  # skip first {start_time} seconds
    cap.set(cv2.CAP_PROP_POS_FRAMES, start_time * 30)
    while cap.isOpened():

        # Press key q to stop
        if cv2.waitKey(1) == ord('q'):
            break

        try:
            # Read frame from the video
            ret, frame = cap.read()
            if not ret:
                break
        except Exception as e:
            print(e)
            continue
        
        # Draw detections
        try:
            detection_with_image(frame)
        except Exception as e:
            print(e)
            continue
    
# Turn-on the worker thread.
if __name__ == '__main__':
    threading.Thread(target=worker, daemon=True).start()
    telegram_bot.start()
    app.run(host='0.0.0.0', port=3000)
