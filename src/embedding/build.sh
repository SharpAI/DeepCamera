#!/bin/bash

LDFLAGS=" -lm -lcompiler_rt" nuitka -j 1  --python-for-scons=/data/data/com.termux/files/usr/bin/python2 --clang --recurse-not-to=tensorflow,numpy,scipy,sklearn,sklearn.model_selection,PIL,six,flask,flask_sqlalchemy,flask_script,flask_migrate,Image,requests,oss2,qiniu,werkzeug.utils,paho.mqtt.client,psutil,billiard,sqlalchemy,celery --recurse-to=facenet,FaceProcessing,faces,objects,align,utilslib,migrate_db,classifier_classify_new  upload_api-v2.py
#LDFLAGS=" -lm -lcompiler_rt" nuitka -j 1 --clang --recurse-not-to=flask,flask_sqlalchemy,flask_script,flask_migrate migrate_db.py
