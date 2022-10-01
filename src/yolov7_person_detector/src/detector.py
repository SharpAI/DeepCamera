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
from telegram_bot import TelegramBot

model_path = "models/yolov7-tiny_480x640.onnx"
yolov7_detector = YOLOv7(model_path, conf_thres=0.6, iou_thres=0.5)

app = Flask(__name__)
q = queue.Queue(1)
def get_parser():
    parser = argparse.ArgumentParser(description="onnx model inference")

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

q = queue.Queue(3)
args = get_parser().parse_args()

telegram_bot = TelegramBot()
previous_person_ts = 0

def detection_with_image(frame):
    global previous_person_ts
    # cv2.imshow('Screen',img)
    # Detect Objects
    KNOWN_COLOR = (255,0,0)
    UNKNOWN_COLOR = (0,0,255)
    bboxes, scores, class_ids = yolov7_detector(frame)
    cropped_imgs, person_bboxes, person_scores, person_class_ids = yolov7_detector.crop_class(frame, bboxes, scores, class_ids, 'person', 80)
    
    pre_colors = []
    unknown = 0
    total = len(cropped_imgs)
    if total > 0:

        for _ in cropped_imgs:
            pre_colors.append(UNKNOWN_COLOR)
        combined_img = yolov7_detector.draw_detections_with_predefined_colors(frame,person_bboxes, person_scores, person_class_ids,pre_colors)

        send_image = False
        if total > 0:
                
            print(f'SharpAI detected {total} person')
            current_ts = time.time()
            if current_ts - previous_person_ts > 5*60:
                send_image = True
                previous_person_ts = current_ts
                telegram_bot.send(f'SharpAI detected {total} person')

        if send_image == True:
            filepath = '/tmp/to_send.jpg'
            cv2.imwrite(filepath,combined_img)
            telegram_bot.send_image(filepath)
        try:
            q.put_nowait(combined_img)
        except queue.Full:
            print('display queue full')

    ret_json = {'unknown':len(cropped_imgs),'total':len(cropped_imgs)}
    return ret_json

def worker():    
    while True:
        item = q.get()
        print(f'Working on {item}')
        
        try:
            cv2.namedWindow("Detection result", cv2.WINDOW_NORMAL)
            cv2.setWindowProperty("Detection result", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
            cv2.imshow("Detection result", item)
            q.task_done()

            if cv2.waitKey(10) & 0xFF == ord('q'):
                cv2.destroyAllWindows()
        except Exception as e:
            print('exception:')
            print(e)
            continue

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
    count = 0
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
            if count % 25 == 0:
                detection_with_image(frame)
            count += 1                
            
        except Exception as e:
            print(e)
            continue
    
# Turn-on the worker thread.
if __name__ == '__main__':
    threading.Thread(target=worker, daemon=True).start()
    telegram_bot.start()
    app.run(host='0.0.0.0', port=3000)
