# -*- coding: utf-8 -*-
import requests
import json
from faces import save_embedding

addr = 'http://localhost:6000/api/embedding'

def get_remote_embedding(embstr):
    # prepare headers for http request
    content_type = 'image/jpeg'
    headers = {'content-type': content_type}
    # send http request with image and receive response
    response = requests.post(addr, data=embstr, headers=headers)
    print(response)
    # decode response
    embedding = json.loads(response.text)['embedding'] 
    print(embedding)
    return save_embedding.convert_string_to_embedding(embedding)
