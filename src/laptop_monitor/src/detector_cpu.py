import os
import threading
import queue
import json

from pymilvus import (connections, CollectionSchema, 
                      FieldSchema, DataType, Collection, utility)

import redis

from img2vec_pytorch import Img2Vec
from PIL import Image
import cv2

from LabelStudioClient import LabelStudioClient

from flask import Flask
from flask import request
from flask import jsonify

app = Flask(__name__)
q = queue.Queue(1)

connections.connect(host="milvus", port=19530)
red = redis.Redis(host='redis', port=6379, db=0)
red.flushdb()
collection_name = "image_similarity_search"

dim = 512
default_fields = [
    FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
    FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=dim)
]
default_schema = CollectionSchema(fields=default_fields, description="Image test collection")
collection = Collection(name=collection_name, schema=default_schema)

if not utility.has_collection(collection_name):
    default_index = {"index_type": "IVF_SQ8", "params": {"nlist": 512}, "metric_type": "L2"}
    collection.create_index(field_name="vector", index_params=default_index)
collection.load()

img2vec = Img2Vec(cuda=False)
import threading
import queue

q = queue.Queue(1)

def worker():
    cv2.namedWindow("Screen", cv2.WINDOW_NORMAL)
    cv2.setWindowProperty("Screen", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    
    while True:
        item = q.get()
        print(f'Working on {item}')
        
        img = cv2.imread(item, cv2.IMREAD_ANYCOLOR)
        cv2.imshow("Screen", img)

        if cv2.waitKey(25) & 0xFF == ord('q'):
            cv2.destroyAllWindows()
            cv2.namedWindow("Screen", cv2.WINDOW_NORMAL)
            cv2.setWindowProperty("Screen", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    
        print(f'Finished {item}')
        q.task_done()
        os.remove(item)
        
@app.route('/submit/image', methods=['POST'])
def submit_image():
    json_data = json.loads(request.data)

    camera_id = json_data['camera_id']
    filename = json_data['filename']
    print(f'filename: {filename}, camera_id: {camera_id}')

    # Read in an image (rgb format)
    img = Image.open(filename)
    # Get a vector from img2vec, returned as a torch FloatTensor
    vec = img2vec.get_vec(img, tensor=False)
    # print(vec.shape)

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
            
            if res.distance < 2:
                insert = False
                break
    if insert == True:
        mr = collection.insert([[vec]])
        ids = mr.primary_keys
        LabelStudioClient.create_task_with_file(filename)
        # print(ids)
        # for x in range(len(ids)):
        #     red.set(str(ids[x]), paths[x])
        try:
            q.put_nowait(filename)
        except queue.Full:
            print('queue full')
    else:
        os.remove(filename)
    return 'ok', 200
# Turn-on the worker thread.
threading.Thread(target=worker, daemon=True).start()
app.run(host='0.0.0.0', port=3000)
