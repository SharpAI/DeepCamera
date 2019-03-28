# -*- coding:utf-8 -*-
from upload_api import db


class People(db.Model):
    __tablename__ = 'people'
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(64))
    name = db.Column(db.String(64))
    embed = db.Column(db.PickleType)  # 存储任何Python对象，自动序列化
    # filename = db.Column(db.String(64))
    # local_url = db.Column(db.String(128))
    aliyun_url = db.Column(db.String(128))

    def __repr__(self):
        return '<People {}>'.format(self.id)


class TrainSet(db.Model):
    __tabelname__ = 'TrainSet'
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(128), index=True)
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
