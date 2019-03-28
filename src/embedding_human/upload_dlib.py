# coding=utf-8
import tensorflow as tf
import os, json, time
import numpy as np
from scipy import misc

from flask import Flask, request, url_for, make_response, abort, Response, jsonify, send_from_directory, redirect
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename

import facenet
import align.detect_face
import FaceProcessing
from save2gst import save2gst
from utilslib.aliyunUpload import aliyunUploadInit
from utilslib.aliyunUpload import aliyun_upload_img

# For Dlib Alignment
import cv2
from align import align_dlib

BASEDIR = os.getenv('RUNTIME_BASEDIR',os.path.abspath(os.path.dirname(__file__)))
UPLOAD_FOLDER = os.path.join(BASEDIR, 'image')
DATABASE = 'sqlite:///' + os.path.join(BASEDIR, 'data.sqlite')

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif', 'bitmap'])

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

db = SQLAlchemy(app)

image_size = 160
margin = 2
minsize = 20  # minimum size of face
threshold = [0.6, 0.7, 0.7]  # three steps's threshold
factor = 0.709  # scale factor
confident_value = 0.78

USE_MTCNN = True
USE_DLIB = False

sess, graph = FaceProcessing.InitialFaceProcessor()

if USE_MTCNN:
    graph2 = tf.Graph()
    with graph2.as_default():
        sess2 = tf.Session(config=tf.ConfigProto(log_device_placement=False), graph=graph2)
        with sess2.as_default():
            pnet, rnet, onet = align.detect_face.create_mtcnn(sess2, None)
if USE_DLIB:
    dlibFacePredictor = os.path.join(BASEDIR,'../models',
                                     "shape_predictor_68_face_landmarks.dat")
    dlibAlign = align_dlib.AlignDlib(dlibFacePredictor)

def load_align_image(image_path, sess, graph, pnet, rnet, onet):
    img = misc.imread(os.path.expanduser(image_path))
    img_size = np.asarray(img.shape)[0:2]

    with graph2.as_default():
        # sess2 = tf.Session(config=tf.ConfigProto(log_device_placement=False))
        with sess2.as_default():
            bounding_boxes, _ = align.detect_face.detect_face(img, minsize, pnet, rnet, onet, threshold, factor)
    nrof_faces = bounding_boxes.shape[0]
    width = img_size[1]
    height = img_size[0]
    if nrof_faces > 0:
        det = np.squeeze(bounding_boxes[0, 0:4])
        bb = np.zeros(4, dtype=np.int32)
        bb[0] = np.maximum(det[0] - margin / 2, 0)
        bb[1] = np.maximum(det[1] - margin / 2, 0)
        bb[2] = np.minimum(det[2] + margin / 2, img_size[1])
        bb[3] = np.minimum(det[3] + margin / 2, img_size[0])
        if bb[0] == 0 or bb[1] == 0 or bb[2] >= width or bb[3] >= height:
            print('Out of boundary')
            return None
        print(bb)
        print(img_size)
        if USE_DLIB:
            rgbImg = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            aligned = dlibAlign.align(160, rgbImg, bb)
        else:
            cropped = img[bb[1]:bb[3], bb[0]:bb[2], :]
            aligned = misc.imresize(cropped, (image_size, image_size), interp='bilinear')
        
        prewhitened = facenet.prewhiten(aligned)
        return prewhitened
    return None
def dlibImageProcessor(imgPath):
    bgrImg = cv2.imread(imgPath)
    if bgrImg is None:
        raise Exception("Unable to load image: {}".format(imgPath))
    rgbImg = cv2.cvtColor(bgrImg, cv2.COLOR_BGR2RGB)
    # assert np.isclose(norm(rgbImg), 11.1355)

    bb = dlibAlign.getLargestFaceBoundingBox(rgbImg)
    #print(bb)
    if bb is not None:
        alignedFace = dlibAlign.align(160, rgbImg, bb)
        prewhitened = facenet.prewhiten(alignedFace)
        #plt.imshow(alignedFace)
        #plt.show()
        return alignedFace
    return None

def featureCalculation(imgpath):
    if USE_MTCNN:
        img_data = load_align_image(imgpath, sess, graph, pnet, rnet, onet)
        if img_data is not None:
            with graph.as_default():
                with sess.as_default():
                    embedding = FaceProcessing.FaceProcessingImageData(img_data, sess, graph)[0]
            return embedding
    if USE_DLIB:
        img_data = dlibImageProcessor(imgpath)
        if img_data is not None:
            with graph.as_default():
                with sess.as_default():
                    embedding = FaceProcessing.FaceProcessingImageData(img_data, sess, graph)[0]
            return embedding

class People(db.Model):
    __tablename__ = 'people'
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(64))
    name = db.Column(db.String(64))
    embed = db.Column(db.PickleType)  # 存储任何Python对象，自动序列化
    # filename = db.Column(db.String(64))
    local_url = db.Column(db.String(128))
    aliyun_url = db.Column(db.String(128))

    def __repr__(self):
        return '<People {}>'.format(self.id)


def updatePeopleImgURL(ownerid, url):
    if len(url) < 1:
        return
    print(ownerid)
    print(url)
    with app.app_context():
        man = People.query.filter_by(id=ownerid).first()
        man.aliyun_url = url
        db.session.add(man)
        db.session.commit()
        # db.session.query(People).filter(People.id == id).update({People.aliyun_url: url})
        # db.session.commit()


"""
def dumps_embed(data):
    return pickle.dumps(data)


def loads_embed(str):
    return pickle.loads(str)


def hash_embed(data):
    md5 = hashlib.md5()
    md5.update(data)
    return md5.hexdigest()
"""


def compare(emb1, emb2):
    dist = np.sqrt(np.sum(np.square(np.subtract(emb1, emb2))))
    # d = emb1 - emb2
    # sqL2 = np.dot(d, d)

    # print("+ Squared l2 distance between representations: {:0.3f}, dist is {:0.3f}".format(sqL2,dist))
    print("+ distance between representations:  {:0.3f}".format(dist))
    # return sqL2
    return dist


def allowed_file(filename):
    """
    检查文件扩展名是否合法
    :param filename:
    :return: 合法 为 True
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


@app.route('/api/images/<filename>', methods=['GET'])
def img(filename):
    # p = People.query.filter_by(filename=filename).first()
    # if p and p.aliyun_url:
    #     return redirect(p.aliyun_url)
    if os.path.isfile(os.path.join(app.config['UPLOAD_FOLDER'], filename)):
        # 返回图片
        return send_from_directory(app.config['UPLOAD_FOLDER'],
                                   filename)
        # 返回json
        # data = {'img_name': filename, 'img_url': request.url}
        # js = json.dumps(data)
        # resp = Response(js, status=200, mimetype='application/json')
        # return resp

    else:
        return abort(404)


@app.route('/api/images/', methods=['POST'])
def upload_img():
    f = request.files['file']  # 从表单的file字段获取文件，file为该表单的name值
    if f and allowed_file(f.filename):  # 检查扩展名合法
        filename = secure_filename(f.filename)  # 修改成安全文件名
        ext = filename.rsplit('.', 1)[1]  # 获取文件后缀
        unix_time = int(time.time())
        uuid = request.args.get('uuid', '')
        new_filename = uuid + str(unix_time) + '.' + ext  # 修改了上传的文件名
        imagepath = os.path.join(app.config['UPLOAD_FOLDER'], new_filename)
        f.save(imagepath)
        local_url = url_for('img', filename=new_filename, _external=True)
        with graph.as_default():
            # sess2 = tf.Session(config=tf.ConfigProto(log_device_placement=False))
            with sess.as_default():
                embedding = FaceProcessing.FaceProcessingOne(imagepath, sess, graph)[0]

        # dumps_data = dumps_embed(embedding)  # json序列化
        people = People.query.all()  # 数据库中所有的行
        for p in people:
            if compare(embedding, p.embed) < confident_value:  # 比较, 小于confident_value认为同一个人
                people = p
                print(">>> same people: %d" % p.id)
                break
        else:
            people = People(embed=embedding, uuid=uuid)
            db.session.add(people)
            db.session.commit()
            print(">>> new people")

        p_id = people.id  # 识别出用户ID
        people.aliyun_url = uploadImg.aliyun_upload_img(imagepath, 4)
        # uploadImg.newjob(id, imagepath)  # 异步线程上传图片到aliyun
        people.local_url = local_url  # 为ID对应的用户更新刚上传的图片

        data = {'img_name': new_filename,
                'local_url': local_url,
                'aliyun_url': people.aliyun_url,
                'errorn': 0,
                'id': p_id,
                'uuid': uuid,
                }  # 上传成功
        js = json.dumps(data)
        resp = Response(js, status=200, mimetype='application/json')

        if people.aliyun_url:  # 优先发送aliyun的图片地址
            url = people.aliyun_url
        else:
            url = people.local_url
        save2gst(uuid, id, url)  # 调用故事帖api保存
        return resp
    else:
        return jsonify({"errno": 1001, "message": "上传失败"})


@app.route('/api/fullimg/', methods=['POST'])
def upload_full_img():
    f = request.files['file']
    if f and allowed_file(f.filename):
        ext = f.filename.rsplit('.', 1)[1]
        unix_time = int(time.time())
        uuid = request.args.get('uuid', '')
        filename = uuid + str(unix_time) + '.' + ext
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        f.save(image_path)

        if USE_MTCNN:
            img_data = load_align_image(image_path, sess, graph, pnet, rnet, onet)
        if USE_DLIB:
            img_data = dlibImageProcessor(image_path)
        if img_data is not None:
            # print("Image Shape is ",img_data.shape)
            with graph.as_default():
                with sess.as_default():
                    embedding = FaceProcessing.FaceProcessingImageData(img_data, sess, graph)[0]
            # print('Embedding of Full Image is %s' %embedding)

            # 同步阻塞
            people = People.query.all()
            if people:
                min_value = min([(compare(embedding, p.embed), p.id) for p in people])  # 遍历数据库并求最小compare值
                print(min_value)
                if min_value[0] < confident_value:
                    people = People.query.filter_by(id=min_value[1]).first()
                    print(">>> same people: %d" % min_value[1])
                else:
                    people = People(embed=embedding, uuid=uuid)
                    db.session.add(people)
                    db.session.commit()
                    print(">>> new people")
            else:
                people = People(embed=embedding, uuid=uuid)
                db.session.add(people)
                db.session.commit()
                print(">>> new people")
            # people.filename = filename
            local_url = url_for('img', filename=filename, _external=True)
            people.local_url = local_url
            aliyun_url = aliyun_upload_img(image_path, 4)
            people.aliyun_url = aliyun_url
            db.session.add(people)
            db.session.commit()

            #if len(aliyun_url) > 1:  # 优先发送aliyun的图片地址
                #save2gst(uuid, people.id, aliyun_url)  # 发送请求给workai

            data = {'error': 0,
                    'img_name': filename,
                    'id': people.id,
                    'uuid': people.uuid,
                    'aliyun_url': aliyun_url,
                    }
            resp = Response(json.dumps(data), status=200, mimetype='application/json')
            print('-----------------')
            return resp
        else:
            print 'No available face in this image'
            print '-----------------------'
            os.remove(image_path)
            return jsonify({"error": 1001, "message": u"识别失败"})
    else:
        return jsonify({'error': 1001, 'message': u'上传失败'})


@app.errorhandler(404)
def not_found(error=None):
    message = {
        'status': 404,
        'message': 'Not Found ' + request.url,
    }
    return make_response(json.dumps(message), 404)


# 测试上传
@app.route('/test/upload')
def upload_test():
    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form method=post action=/api/images enctype=multipart/form-data>
      <p><input type=file name=file>
         <input type=submit value=Upload>
    </form>
    '''


# flask默认的启动
if __name__ == '__main__':
    uploadImg = aliyunUploadInit(updatePeopleImgURL)

    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    if not os.path.exists(os.path.join(BASEDIR, 'data.sqlite')):
        db.create_all()

    # do nothing, just warm up
    featureCalculation('./image/Mike_Alden_0001.png')
    app.run(host='0.0.0.0',port=2999)

# gunicorn启动时创建文件
# if not os.path.exists(UPLOAD_FOLDER):
#     os.makedirs(UPLOAD_FOLDER)
#
# if not os.path.exists(os.path.join(BASEDIR, 'data.sqlite')):
#     db.create_all()
