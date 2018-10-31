# -*- coding: UTF-8 -*-
import os
import numpy as np
from migrate_db import People, db, app


uuid = '28DDU17531000102'
embedding_basedir = '/home/actiontec/PycharmProjects/DeepLearning/FaceRecognition/facenet/src/faces/' \
                    'ae64c98bdff9b674fb5dad4b/front/face_embedding'
url = ''
style = 'front'
group_id = 'ae64c98bdff9b674fb5dad4b'


def txt2embedding(file_path):
    with open(file_path, 'r') as bottleneck_file:
        bottleneck_string = bottleneck_file.read()
        # print(bottleneck_string)
        bottleneck_values = [float(x) for x in bottleneck_string.split(',')]
        embedding = np.array(bottleneck_values,  dtype='f')
        return embedding


if __name__ == '__main__':
    with app.app_context():
        for root, dirs, files in os.walk(embedding_basedir):
            for name in files:
                file_path = os.path.join(root, name)
                objid = root.split('_')[-1]
                embedding = txt2embedding(file_path)
                people = People(embed=embedding, uuid=uuid, group_id=group_id,
                                objId=objid, aliyun_url=url, classId=objid, style=style)
                db.session.add(people)
        db.session.commit()
