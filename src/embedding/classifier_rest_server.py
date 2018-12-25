# -*- coding: utf-8 -*-
import time,os,json
import numpy as np

from flask import Flask, jsonify, request, abort
import classifier_classify_new as classifer
from faces import save_embedding
from celery import Celery
from celery import Task
from celery.concurrency import asynpool

from utilslib.getDeviceInfo import get_current_groupid, get_deviceid 
from recognition import face_recognition_on_embedding

asynpool.PROC_ALIVE_TIMEOUT = 60.0 #set this long enough

REDIS_ADDRESS = os.getenv('REDIS_ADDRESS','redis')

TASKER=os.getenv('TASKER','worker')
deepeye = Celery('classify',
    broker='redis://guest@'+REDIS_ADDRESS+'/0',
    backend='redis://guest@'+REDIS_ADDRESS+'/0')
deepeye.count = 1


app = Flask(__name__)

@app.route('/classify', methods=['POST'])
def classify_task():
    if not request.json:
        abort(400)
    req_data = request.get_json()
    print(req_data)
    embedding_path = req_data['embedding_path']
    classifier_filename = req_data['classifier_filename']

    emb = save_embedding.read_embedding_string(embedding_path)
    emb = np.asarray(emb)

    result = classifer.classify([emb], classifier_filename, None)
    #_, human_string, score, top_three_name = classifer.classify(emb, classifier_filename, None)
    return jsonify({'status': 'ok','result':result}), 200

@app.route('/classify_full', methods=['POST'])
def classify_full():
    if not request.json:
        abort(400)
    req_data = request.get_json()
    print(req_data)

    return jsonify({'status': 'ok','result':result}), 200

@app.route('/train', methods=['POST'])
def train_task():
    if not request.json:
        abort(400)
    req_data = request.get_json()
    print(req_data)
    args_list = req_data['args_list']
    result = classifer.train_svm_with_embedding(args_list)
    #_, human_string, score, top_three_name = classifer.classify(emb, classifier_filename, None)
    return jsonify({'status': 'ok','result':result}), 200

@app.route("/", methods=["GET"])
def root():
    return jsonify({'status','ok'}), 200

@deepeye.task
def classify(image):
    print(">>> extract() {} ".format(image))
    embedding_path=image["embedding_path"]
    imgpath=image["path"]
    style=image["style"]
    blury=image["blury"]
    ts=image["ts"]
    trackerid=image["trackerid"]
    totalPeople=image["totalPeople"]
    uuid = get_deviceid()
    current_groupid = get_current_groupid()

    if current_groupid is None:
        return json.dumps({"result": {"style": "", "url": "", "face_fuzziness": 5, "recognized": False, "detected": True, "face_id": "", "accuracy": 0}})

    timestamp1 = time.time()

    result={}

    if embedding_path is not None:
        if type(trackerid) is not str:
            trackerid = str(trackerid)
        embedding = save_embedding.read_embedding_string(embedding_path)
        embedding = np.asarray(embedding)
        result, api_data = face_recognition_on_embedding(imgpath, embedding, totalPeople, blury, uuid, current_groupid, style, trackerid, timestamp1, ts, embedding_path)

    return json.dumps({'result': result,'api_data': api_data})

deepeye.conf.task_routes = {
    'classify.classify': {'queue': 'classify'}
}
if __name__ == '__main__':
    if TASKER == "worker":
        deepeye.start()
    else:
        print('starting flask..')
        app.run(port=5050,host="0.0.0.0")
