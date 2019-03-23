# -*- coding: utf-8 -*-
import os
from flask import Flask, request, jsonify
import FaceProcessing
from faces import save_embedding
# Initialize the Flask application
app = Flask(__name__)
# route http posts to this method
BASEDIR = os.getenv('RUNTIME_BASEDIR',os.path.abspath(os.path.dirname(__file__)))

@app.route('/api/embedding', methods=['POST'])
def embedding():
    embedding = FaceProcessing.FaceProcessingBase64ImageData2(request.data)
    embedding_str = save_embedding.convert_embedding_to_string(embedding)
    print(embedding_str)
    return jsonify({'embedding':embedding_str}), 200
if __name__ == '__main__':
    FaceProcessing.init_embedding_processor()
    print("start to warm up")
    embedding = FaceProcessing.FaceProcessingImageData2(os.path.join(BASEDIR,"image","Mike_Alden_0001_tmp.png"))
    print("warmed up")
    print(embedding)
    app.run(host="0.0.0.0", port=6000)
