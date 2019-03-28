# coding=utf-8
# https://github.com/solderzzc/DeepLearning/wiki/Flask-migrate-db
# 使用该脚本进行数据库迁移，迁移前需要用upload_api脚本下的最新的数据库model类覆盖下面

import os

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_script import Manager, Server
from flask_migrate import Migrate, MigrateCommand

BASEDIR = os.getenv('RUNTIME_BASEDIR',os.path.abspath(os.path.dirname(__file__)))
# UPLOAD_FOLDER = os.path.join(BASEDIR, 'image')
DATABASE = 'sqlite:///' + os.path.join(BASEDIR, 'data', 'data.sqlite')

app = Flask('__main__')  # resolve nuitka bug
# app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS' ] = True

db = SQLAlchemy(app)
manager = Manager(app)
migrate = Migrate(app=app, db=db)
manager.add_command('db', MigrateCommand)
# manager.add_command('runserver', Server(host='0.0.0.0', port=5000))


class People(db.Model):
    __tablename__ = 'people'
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(64))
    group_id = db.Column(db.String(64))
    objId = db.Column(db.String(64))
    classId = db.Column(db.String(64))
    embed = db.Column(db.PickleType)  # 存储任何Python对象，自动序列化
    # filename = db.Column(db.String(64))
    # local_url = db.Column(db.String(128))
    aliyun_url = db.Column(db.String(128))
    style = db.Column(db.String(64))

    def __repr__(self):
        return '<People id={} uuid={} group_id={} objid={} classId={} aliyun_url={} style={}>'.format(self.id, self.uuid, self.group_id, self.objId, self.classId, self.aliyun_url, self.style)


class TrainSet(db.Model):
    __tabelname__ = 'TrainSet'
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(128), index=True)
    group_id = db.Column(db.String(128))
    embed = db.Column(db.PickleType)
    is_or_isnot = db.Column(db.Boolean, default=True)
    person_id = db.Column(db.String(64))  # workai提供
    device_id = db.Column(db.String(64))
    face_id = db.Column(db.String(64))
    filepath = db.Column(db.String(128))
    style = db.Column(db.String(64))
    drop = db.Column(db.Boolean, default=True)

    def __repr__(self):
        if self.is_or_isnot:
            return '<({}) is ({}) droped= ({}) group_id=({}) filepath=({})>'.format(self.url, self.face_id, self.drop, self.group_id, self.filepath)
        else:
            return '<({}) is not ({}) droped= ({}) group_id=({}) filepath=({})>'.format(self.url, self.face_id, self.drop, self.group_id, self.filepath)


class AutoGroupSet(db.Model):
    __tabelname__ = 'AutoGroupSet'
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(128), index=True)
    group_id = db.Column(db.String(128))
    device_id = db.Column(db.String(64))
    embed = db.Column(db.PickleType)
    is_or_isnot = db.Column(db.Boolean, default=True)
    person_id = db.Column(db.String(64))
    face_id = db.Column(db.String(64))
    unique_face_id = db.Column(db.String(64))
    style = db.Column(db.String(64))
    filepath = db.Column(db.String(512))

    def __repr__(self):
        if self.is_or_isnot:
            return '<({}) is ({})>'.format(self.url, self.face_id)
        else:
            return '<({}) is not ({})>'.format(self.url, self.face_id)

class Stranger(db.Model):
    __tablename__ = 'stranger'
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(64))
    group_id = db.Column(db.String(64))
    objId = db.Column(db.String(64))
    classId = db.Column(db.String(64))
    embed = db.Column(db.PickleType)
    aliyun_url = db.Column(db.String(128))
    style = db.Column(db.String(64))
#     last_time = db.Column(db.Date, default=datetime.utcnow)

    def __repr__(self):
        return '<People id={} uuid={} group_id={} objid={} classId={} url={} style={} time={}>'.format(self.id, self.uuid, self.group_id, self.objId, self.classId, self.aliyun_url, self.style)

class Frame(db.Model):
    __tablename__ = 'frame'
    id = db.Column(db.Integer, primary_key=True)
    camera_id = db.Column(db.String(64))
    group_id = db.Column(db.String(64))
    blury = db.Column(db.Integer)
    img_path = db.Column(db.String(128))
    img_style = db.Column(db.String(64))
    accuracy = db.Column(db.Float)
    url = db.Column(db.String(128))
    num_face = db.Column(db.Integer)
    tracking_id = db.Column(db.String(64))
    device_id = db.Column(db.String(64))
    time_stamp = db.Column(db.Integer)
    tracking_flag = db.Column(db.String(64))

    def __repr__(self):
        return '<Frame id={} camera_id={} group_id={} blury={} img_path={} img_style={} accuracy={} url={} num_face={} tracking_id={} device_id={} time_stamp={} tracking_flag={}>'.format(
                       self.id, self.camera_id, self.group_id, self.blury,
                       self.img_path, self.img_style, self.accuracy, self.url,
                       self.num_face, self.tracking_id, self.device_id, self.time_stamp,
                       self.tracking_flag)

if __name__ == '__main__':
    db.create_all()
    manager.run()
