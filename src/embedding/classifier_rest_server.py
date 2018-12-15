# -*- coding: utf-8 -*-

import numpy as np

from flask import Flask, jsonify, request, abort
import classifier_classify_new as classifer
from faces import save_embedding
#from recognition import face_recognition_on_embedding

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

if __name__ == '__main__':
    app.run(debug=True, port=5050,host="0.0.0.0",processes=2)
