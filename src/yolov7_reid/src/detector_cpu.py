import os
import queue
import json
import argparse
import threading
import pafy
# from pymilvus import (connections, CollectionSchema, 
#                       FieldSchema, DataType, Collection, utility)
# import redis

# from PIL import Image
import numpy as np
import cv2
import onnxruntime

#from LabelStudioClient import LabelStudioClient

from flask import Flask
from flask import request
from flask import jsonify
from YOLOv7 import YOLOv7

model_path = "models/yolov7-tiny_480x640.onnx"
yolov7_detector = YOLOv7(model_path, conf_thres=0.3, iou_thres=0.5)

app = Flask(__name__)
q = queue.Queue(1)
def get_parser():
    parser = argparse.ArgumentParser(description="onnx model inference")

    parser.add_argument(
        "--model-path",
        default="./models/fast-reid_mobilenetv2.onnx",
        help="onnx model path"
    )
    parser.add_argument(
        "--height",
        type=int,
        default=256,
        help="height of image"
    )
    parser.add_argument(
        "--width",
        type=int,
        default=128,
        help="width of image"
    )
    return parser
# connections.connect(host="milvus", port=19530)
# red = redis.Redis(host='redis', port=6379, db=0)
# red.flushdb()
# collection_name = "yolov7_reid"

# dim = 512
# default_fields = [
#     FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
#     FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=dim)
# ]
# default_schema = CollectionSchema(fields=default_fields, description="Image test collection")
# collection = Collection(name=collection_name, schema=default_schema)

# if not utility.has_collection(collection_name):
#     default_index = {"index_type": "IVF_SQ8", "params": {"nlist": 512}, "metric_type": "L2"}
#     collection.create_index(field_name="vector", index_params=default_index)
# collection.load()

def preprocess(image_path, image_height, image_width):
    original_image = cv2.imread(image_path)
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

def detection_with_image(image):
    # cv2.imshow('Screen',img)
    # Detect Objects
    bboxes, scores, class_ids = yolov7_detector(image)
    cropped_imgs, person_bboxes, person_scores, person_class_ids = yolov7_detector.crop_class(image, bboxes, scores, class_ids, 'person', 20)
    print(f'{len(cropped_imgs)} person detected')

    combined_img = yolov7_detector.draw_detections(image,person_bboxes, person_scores, person_class_ids)
    cv2.namedWindow("Screen", cv2.WINDOW_NORMAL)
    cv2.setWindowProperty("Screen", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    cv2.imshow("Screen", combined_img)

    if cv2.waitKey(25) & 0xFF == ord('q'):
        cv2.destroyAllWindows()

def worker():
    input_name = ort_sess.get_inputs()[0].name
    
    while True:
        item = q.get()
        print(f'Working on {item}')
        
        try:
            img = cv2.imread(item,cv2.IMREAD_ANYCOLOR)
            print(img)

            # Draw detections
            detection_with_image(img)
            #image = preprocess(path, args.height, args.width)
            #feat = ort_sess.run(None, {input_name: image})[0]
            #feat = normalize(feat, axis=1)

        except Exception as e:
            print('exception:')
            print(e)
            continue

        print(f'Finished {item}')
        q.task_done()
        # os.remove(item)

@app.route('/submit/image', methods=['POST'])
def submit_image():
    json_data = json.loads(request.data)

    camera_id = json_data['camera_id']
    filename = json_data['filename']
    print(f'filename: {filename}, camera_id: {camera_id}')

    try:
        q.put_nowait(filename)
    except queue.Full:
        print('queue full')

    # os.remove(filename)
    return 'ok', 200

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
        detection_with_image(frame)
        # Update object localizer
        # bboxes, scores, class_ids = yolov7_detector(frame)
        # cropped_imgs,person_bboxes,person_scores,person_class_ids = yolov7_detector.crop_class(frame, bboxes, scores, class_ids, 'person', 20)
        # combined_img = yolov7_detector.draw_detections(frame,person_bboxes, person_scores, person_class_ids)
        # cv2.imshow("Detected Objects", combined_img)
    
# Turn-on the worker thread.
if __name__ == '__main__':
    threading.Thread(target=worker, daemon=True).start()
    app.run(host='0.0.0.0', port=3000)
