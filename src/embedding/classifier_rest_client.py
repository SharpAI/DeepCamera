# -*- coding: utf-8 -*-

import os
import json
import urllib2

rest_host = os.getenv('REST_CLASSIFIER_HOST','localhost')
rest_port = os.getenv('REST_CLASSIFIER_PORT','5050')

classify_request_url = 'http://'+rest_host+':'+rest_port+'/classify'
train_request_url = 'http://'+rest_host+':'+rest_port+'/train'

def json_load_byteified(file_handle):
    return _byteify(
        json.load(file_handle, object_hook=_byteify),
        ignore_dicts=True
    )

def json_loads_byteified(json_text):
    return _byteify(
        json.loads(json_text, object_hook=_byteify),
        ignore_dicts=True
    )

def _byteify(data, ignore_dicts = False):
    # if this is a unicode string, return its string representation
    if isinstance(data, unicode):
        return data.encode('utf-8')
    # if this is a list of values, return list of byteified values
    if isinstance(data, list):
        return [ _byteify(item, ignore_dicts=True) for item in data ]
    # if this is a dictionary, return dictionary of byteified keys and values
    # but only if we haven't already byteified it
    if isinstance(data, dict) and not ignore_dicts:
        return {
            _byteify(key, ignore_dicts=True): _byteify(value, ignore_dicts=True)
            for key, value in data.iteritems()
        }
    # if it's anything else, return it in its original form
    return data
def classify(emb_array, classifier_filename, embedding_path):
    if not os.path.exists(classifier_filename):
        print('Please check classifier_filename passing to classifer of rest client')
        return -1, None, 0, None
    if not os.path.exists(embedding_path):
        print('Please check embedding path passing to classifer of rest client')
        return -1, None, 0, None

    req = urllib2.Request(classify_request_url)
    req.add_header('Content-Type', 'application/json')
    response = urllib2.urlopen(req, json.dumps({
        'embedding_path': embedding_path,
        'classifier_filename': classifier_filename
    }))
    data = json_load_byteified(response)
    print(data)
    if data['status'] == 'ok':
        return data['result']
    else:
        print('Please check if rest api server of classifer is working')
        return -1, None, 0, None
def train_svm_with_embedding(args_list):
    req = urllib2.Request(train_request_url)
    req.add_header('Content-Type', 'application/json')
    print(args_list)
    response = urllib2.urlopen(req, json.dumps({
        'args_list': args_list
    }))

    data = json_load_byteified(response)

    print(data)
    if data['status'] == 'ok':
        return 'OK'
    return 'Error of classifer service'
