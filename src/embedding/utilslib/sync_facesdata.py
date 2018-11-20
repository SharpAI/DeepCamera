# -*- coding: UTF-8 -*-
import os,sys
BASEDIR = os.path.join(os.getenv('RUNTIME_BASEDIR',os.path.abspath(os.path.join(os.path.dirname(__file__),'../'))))
sys.path.append(BASEDIR)

from faces.save_embedding import download_img_for_svm_sync, get_image_path_sync
from getDeviceInfo import get_current_groupid

from urllib2 import urlopen, URLError, HTTPError
import json

SVM_TRAIN_WITHOUT_CATEGORY=True

if __name__ == '__main__':
    group_id = get_current_groupid()

    #host="http://localhost:3000/restapi/datasync/token/" + str(group_id)
    host = "http://workaihost.tiegushi.com/restapi/datasync/token/" + str(group_id)
    result = None
    try:
        response = urlopen(host, timeout=10)
    except HTTPError as e:
        print('HTTPError: ', e.code)
    except URLError as e:
        print('URLError: ', e.reason)
    except Exception as e:
        print('Error: ', e)
    else:
        # everything is fine
        if 200 == response.getcode():
            result = response.readline()
            #print(result)
            result = json.loads(result)
            for person in result:
                faceId = person.get("faceId")
                urls = person.get("urls")
                print('--> {}'.format(faceId))
                for url in urls:
                    print('        {}'.format(url))
                    # url,faceid 从点圈群相册获取
                    # todo 可以用for循环解析群相册获取的json数据
                    img_url = url['url']
                    face_id = faceId
                    style = url['style']
                    if SVM_TRAIN_WITHOUT_CATEGORY is True:
                        style = 'front'
                    img_path = get_image_path_sync(img_url, group_id, face_id, style)
                    if not os.path.exists(img_path):
                        download_img_for_svm_sync(img_url, group_id, face_id, style)
        else:
            print('response code != 200')
