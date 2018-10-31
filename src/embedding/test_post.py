# -*- coding: UTF-8 -*-
import requests
import time

host = 'http://50.233.238.34:443'
# host = 'http://50.233.238.34:2988'

url = host + '/api/fullimg/'

payload = {'uuid': '7YRBBDB722205800', 'objid': '1'}

files = {'file': open('face_softmax/tmp_data/face_dataset/1_Bachan/01poster10.jpg', 'rb')}

res = requests.post(url=url, params=payload, files=files)

print res.url
print res.status_code