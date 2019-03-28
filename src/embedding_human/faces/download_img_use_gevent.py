# coding=utf-8
# gevent协程批量下载sqlite保存的url
from gevent import monkey; monkey.patch_all()
import gevent
import urllib2
import os
import Image

from models import TrainSet

img_dir = 'face_dataset'
# dataset = TrainSet.query.all()  # 查询所有行，是一个list
dataset_is = TrainSet.query.filter_by(is_or_isnot=True).all()
# dataset_isnot = TrainSet.query.filter_by(is_or_isnot=False).all()


BASE_FOLDER = os.path.join(os.path.abspath(os.getenv('RUNTIME_BASEDIR',os.path.dirname(__file__))), img_dir)

if not os.path.exists(BASE_FOLDER):
    os.makedirs(BASE_FOLDER)


def download_img(url, decice_id, face_id, id):
    print('GET: %s' % url)
    resp_data = urllib2.urlopen(url).read()
    print('%d bytes received from %s.' % (len(resp_data), url))

    folder_name = '{}'.format(face_id)
    folder_path = os.path.join(BASE_FOLDER, folder_name)
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    filename = str(id) + '_' + folder_name + '.png'
    image_path = os.path.join(folder_path, filename)

    if not os.path.isfile(image_path):
        with open(image_path, 'wb') as f:
            f.write(resp_data)
        im = Image.open(image_path)
        im.save(image_path.rsplit('.')[0] + '.jpg')
        os.remove(image_path)

    # return os.path.join(folder_name, filename)


if __name__ == '__main__':
    gevent.joinall([
            gevent.spawn(download_img, data.url, data.device_id, data.face_id, data.id)
        for data in dataset_is
    ])
