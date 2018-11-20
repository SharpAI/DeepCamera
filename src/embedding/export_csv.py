# coding=utf-8
"""
从数据库中导出url并下载，生成csv
"""
import csv, os, urllib

from upload_api import TrainSet

headers = ['path', 'embed', 'is_or_isnot', 'person_id', 'device_id', 'face_id', 'group_id']
# dataset = TrainSet.query.all()  # 查询所有行，是一个list
# dataset_is = TrainSet.query.filter_by(is_or_isnot=True).all()
# dataset_isnot = TrainSet.query.filter_by(is_or_isnot=False).all()


BASE_FOLDER = os.path.join(os.getenv('RUNTIME_BASEDIR',os.path.abspath(os.path.dirname(__file__))), 'dataset')

if not os.path.exists(BASE_FOLDER):
    os.makedirs(BASE_FOLDER)

"""
- [data]
    - [(device_id)_(face_id)]
        - (device_id)_(face_id)_(0001).jpg
        ...
    - []
    - []
"""

def download_img(img_url, decice_id, face_id, i):
    u = urllib.urlopen(img_url)
    foldername = '{}_{}'.format(decice_id, face_id)
    folder_path = os.path.join(BASE_FOLDER, foldername)
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    filename = foldername + str(i) + '.jpg'
    local_path = os.path.join(folder_path, filename)

    if not os.path.isfile(local_path):
        with open(local_path, 'wb') as f:
            f.write(u.read())

    return os.path.join(foldername, filename)



# all export
def all_trainset(dataset):
    rows = [(download_img(d.url, d.device_id, d.face_id, i),
             d.embed, d.is_or_isnot, d.person_id,
             d.device_id, d.face_id, d.group_id)
        for i, d in enumerate(dataset)]

    csv_path = os.path.join(BASE_FOLDER, 'all_dataset.csv')
    with open(csv_path, 'w') as f:
        f_csv = csv.writer(f)
        f_csv.writerow(headers)
        f_csv.writerows(rows)
        print 'export to csv OK!'

# is
def is_trainset(dataset):
    rows = [(download_img(d.url, d.device_id, d.face_id, i),
             d.embed, d.is_or_isnot, d.person_id,
             d.device_id, d.face_id, d.group_id)
            for i, d in enumerate(dataset) if d.is_or_isnot == True]

    csv_path = os.path.join(BASE_FOLDER, 'is_dataset.csv')
    with open(csv_path, 'w') as f:
        f_csv = csv.writer(f)
        f_csv.writerow(headers)
        f_csv.writerows(rows)
        print 'export to csv OK!'


# isnot
def isnot_trainset(dataset):
    rows = [(download_img(d.url, d.device_id, d.face_id, i),
             d.embed, d.is_or_isnot, d.person_id,
             d.device_id, d.face_id, d.group_id)
            for i, d in enumerate(dataset) if d.is_or_isnot == False]

    csv_path = os.path.join(BASE_FOLDER, 'isnot_dataset.csv')
    with open(csv_path, 'w') as f:
        f_csv = csv.writer(f)
        f_csv.writerow(headers)
        f_csv.writerows(rows)
        print 'export to csv OK!'


if __name__ == '__main__':
    all_trainset(dataset=TrainSet.query.all())