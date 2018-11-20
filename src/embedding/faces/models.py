# coding=utf-8
"""
测试用数据库模型
"""
import os
import subprocess

from flask import Flask, request, url_for, make_response, abort, Response, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_script import Manager, Server
from flask_migrate import Migrate, MigrateCommand

BASEDIR = os.path.abspath(os.getenv('RUNTIME_BASEDIR',os.path.dirname(__file__)))
UPLOAD_FOLDER = os.path.join(BASEDIR, 'image')
DATABASE = 'sqlite:///' + os.path.join(BASEDIR, 'data', 'data.sqlite')

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS' ] = True

db = SQLAlchemy(app)
manager = Manager(app)
migrate = Migrate(app=app, db=db)
manager.add_command('db', MigrateCommand)
manager.add_command('runserver', Server(host='0.0.0.0', port=5000))

class People(db.Model):
    __tablename__ = 'people'
    id = db.Column(db.String(64), primary_key=True)
    uuid = db.Column(db.Integer)
    name = db.Column(db.String(64))
    embed = db.Column(db.PickleType)  # 存储任何Python对象，自动序列号
    local_url = db.Column(db.String(128))
    aliyun_url = db.Column(db.String(128))
    bottlenecks = db.Column(db.String(128))
    bottl = db.Column(db.String(128))


    def __repr__(self):
        return '<People {}>'.format(self.id)


class TrainSet(db.Model):
    __tabelname__ = 'TrainSet'
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(128), index=True)
    group_id = db.Column(db.String(128))
    embed = db.Column(db.PickleType)
    is_or_isnot = db.Column(db.Boolean, default=True)
    person_id = db.Column(db.String(64))  # workai提供
    device_id = db.Column(db.Integer)
    face_id = db.Column(db.Integer)

    def __repr__(self):
        if self.is_or_isnot:
            return '<({}) is ({})>'.format(self.url, self.face_id)
        else:
            return '<({}) is not ({})>'.format(self.url, self.face_id)

class AutoGroupSet(db.Model):
    __tabelname__ = 'AutoGroupSet'
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(128), index=True)
    group_id = db.Column(db.String(128))
    embed = db.Column(db.PickleType)
    is_or_isnot = db.Column(db.Boolean, default=True)
    person_id = db.Column(db.String(64))  # workai提供
    device_id = db.Column(db.Integer)
    face_id = db.Column(db.Integer)

    def __repr__(self):
        if self.is_or_isnot:
            return '<({}) is ({})>'.format(self.url, self.face_id)
        else:
            return '<({}) is not ({})>'.format(self.url, self.face_id)


if __name__ == '__main__':
    manager.run()
