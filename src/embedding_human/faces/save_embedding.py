# -*- coding: UTF-8 -*-
import os
try:
    import Image
except:
    from PIL import Image
import shutil
import requests
from requests.adapters import HTTPAdapter
from requests import Session
from io import BytesIO
from scipy import misc
# from models import TrainSet
#
#
# dataset = TrainSet.query.all()
BASEPATH = os.path.abspath(os.path.join(os.getenv('RUNTIME_BASEDIR',os.path.join(os.path.dirname(__file__),os.path.pardir)), 'data', 'faces'))
img_dir = 'face_dataset'
embedding_dir = 'face_embedding'
denoise_dir = 'face_denoise'
# BASE_FOLDER = os.path.join(os.getenv('RUNTIME_BASEDIR',os.path.abspath(os.path.dirname(__file__))), img_dir)
# BOTTLENECKS_FOLDER = os.path.join(os.getenv('RUNTIME_BASEDIR',os.path.abspath(os.path.dirname(__file__))), embedding_dir)

def requests_retry_get(url, timeout=3, retries=3):
    s = Session()
    s.mount('http://', HTTPAdapter(max_retries=retries))
    s.mount('https://', HTTPAdapter(max_retries=retries))
    try:
        return s.get(url, timeout=timeout)
    except Exception as ex:
        print('RequestException ex: ', ex)
        return None

def download_img_only(img_url, dirname):
    image_dir_path = os.path.join(BASEPATH, dirname)
    if not os.path.exists(image_dir_path):
        os.mkdir(image_dir_path)

    r = requests_retry_get(img_url)
    filename = img_url.rsplit('/', 1)[-1] + '.png'
    image_path = os.path.join(image_dir_path, filename)

    if not os.path.isfile(image_path):
        i = Image.open(BytesIO(r.content))
        i.save(image_path)

    return image_path


def download_img(img_url, group_id, face_id, img_id, style):
    group_path = os.path.join(BASEPATH, group_id, style)
    image_dir_path = os.path.join(group_path, 'face_dataset')
    embedding_dir_path = os.path.join(group_path, "face_embedding")
    if not os.path.exists(group_path):
        # os.mkdir(group_path)
        # os.mkdir(image_dir_path)
        # os.mkdir(embedding_dir_path)
        shutil.copytree(os.path.join(BASEPATH, 'tmp_data'), group_path)

    foldername = '{}_{}'.format(group_id, face_id)
    folder_path = os.path.join(image_dir_path, foldername)
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    # r = requests.get(img_url)
    r = requests_retry_get(img_url)
    filename = img_url.rsplit('/', 1)[-1] + '.png'
    image_path = os.path.join(folder_path, filename)

    if not os.path.isfile(image_path):
        i = Image.open(BytesIO(r.content))
        i.save(image_path)
    return image_path


def download_img_for_svm(img_url, group_id, face_id, style):
    image_path = get_image_path(img_url, group_id, face_id, style)
    try:
        # r = requests.get(img_url, timeout=10)
        r = requests_retry_get(img_url, timeout=10)
    except Exception as ex:
        print('RequestException ex: ', ex)
        return None
    else:
        if r.status_code == 200:
            if not os.path.isfile(image_path):
                i = Image.open(BytesIO(r.content))
                i.save(image_path)
            return image_path
        else:
            print('error')
            return None


def get_image_path(img_url, group_id, face_id, style):
    group_path = os.path.join(BASEPATH, group_id, style)
    image_dir_path = os.path.join(group_path, 'face_dataset')
    embedding_dir_path = os.path.join(group_path, "face_embedding")
    if not os.path.exists(group_path):
        os.makedirs(group_path)
        os.mkdir(image_dir_path)
        os.mkdir(embedding_dir_path)

    foldername = '{}_{}'.format(group_id, face_id)
    folder_path = os.path.join(image_dir_path, foldername)
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    filename = img_url.rsplit('/', 1)[-1] + '.png'
    image_path = os.path.join(folder_path, filename)
    return image_path

def download_img_for_svm_sync(img_url, group_id, face_id, style):
    image_path = get_image_path_sync(img_url, group_id, face_id, style)
    try:
        # r = requests.get(img_url, timeout=10)
        r = requests_retry_get(img_url, timeout=10)
    except requests.exceptions.Timeout:
        print('Request timed out.')
        return None
    else:
        if r.status_code == 200:
            if not os.path.isfile(image_path):
                i = Image.open(BytesIO(r.content))
                i.save(image_path)
            return image_path
        else:
            print('error')
            return None


def get_image_path_sync(img_url, group_id, face_id, style):
    group_path = os.path.join(BASEPATH, group_id+'_sync', style)
    image_dir_path = os.path.join(group_path, 'face_dataset')
    embedding_dir_path = os.path.join(group_path, "face_embedding")
    if not os.path.exists(group_path):
        os.makedirs(group_path)
        os.mkdir(image_dir_path)
        os.mkdir(embedding_dir_path)

    foldername = '{}_{}'.format(group_id, face_id)
    folder_path = os.path.join(image_dir_path, foldername)
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    filename = img_url.rsplit('/', 1)[-1] + '.png'
    image_path = os.path.join(folder_path, filename)
    return image_path


def download_img_for_svm_dst(img_url, group_id, face_id, style, dst):
    image_path = get_image_path_dst(img_url, group_id, face_id, style, dst)
    try:
        # r = requests.get(img_url, timeout=10)
        r = requests_retry_get(img_url, timeout=10)
    except requests.exceptions.Timeout:
        print('Request timed out.')
        return None
    else:
        if r.status_code == 200:
            if not os.path.isfile(image_path):
                i = Image.open(BytesIO(r.content))
                i.save(image_path)
            return image_path
        else:
            print('error')
            return None

def get_image_path_dst(img_url, group_id, face_id, style, dst):
    group_path = os.path.join(BASEPATH, group_id+"_"+dst, style)
    image_dir_path = os.path.join(group_path, 'face_dataset')
    embedding_dir_path = os.path.join(group_path, "face_embedding")
    if not os.path.exists(group_path):
        os.makedirs(group_path)
        os.mkdir(image_dir_path)
        os.mkdir(embedding_dir_path)

    foldername = '{}_{}'.format(group_id, face_id)
    folder_path = os.path.join(image_dir_path, foldername)
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    filename = img_url.rsplit('/', 1)[-1] + '.png'
    image_path = os.path.join(folder_path, filename)
    return image_path

def get_image_denoise_path(img_path):
    denoise_dir_path = img_path.rsplit('/', 1)[0].replace(img_dir, denoise_dir)
    if not os.path.exists(denoise_dir_path):
        os.makedirs(denoise_dir_path)
    denoise_path = img_path.replace(img_dir, denoise_dir)
    return denoise_path

def save_image_denoise(img, img_path):
    imgdir = os.path.dirname(img_path)
    if not os.path.exists(imgdir):
        os.makedirs(imgdir)
    misc.imsave(img_path, img)

def get_embedding_path(img_path):
    embedding_dir_path = img_path.rsplit('/', 1)[0].replace(img_dir, embedding_dir)
    if not os.path.exists(embedding_dir_path):
        os.makedirs(embedding_dir_path)
    embedding_path = img_path.replace(img_dir, embedding_dir) + '.txt'
    return embedding_path

def get_embedding_path_for_worker(img_path):
    embedding_path = img_path+'.txt'
    return embedding_path

def create_embedding_string(embedding, embedding_path):
    embedding_string = ','.join(str(x) for x in embedding)
    with open(embedding_path, 'w') as bottleneck_file:
        bottleneck_file.write(embedding_string)
    print('Finish create a embedding_string_file')

def read_embedding_string(embedding_path):
    with open(embedding_path, 'r') as bottleneck_file:
        embedding_string_array = bottleneck_file.read().split(",")
        embedding_array = [ float(s) for s in embedding_string_array ]
        #print("embedding_array={}".format(embedding_array))
        return embedding_array
def convert_embedding_to_string(embedding):
    embedding_string = ','.join(str(x) for x in embedding)
    return embedding_string

def convert_string_to_embedding(embedding_string):
    embedding_string_array = embedding_string.split(",")
    embedding_array = [ float(s) for s in embedding_string_array ]
    return embedding_array

def down_embedding(embedding_url, embedding_path):
    try:
        # r = requests.get(embedding_url, timeout=10)
        r = requests_retry_get(embedding_url, timeout=10)
    except requests.exceptions.Timeout:
        print('Request timed out.')
        return None
    else:
        if r.status_code == 200:
            c = r.content
            #FIXME: 这里下载的embeding有可能是空的,加个判断
            if c is None:
                return None
            with open(embedding_path, 'wb') as f:
                f.write(c)
            return embedding_path
        else:
            print('{"error":"Document not found"}')
            return None
            # start 计算embedding
