# coding=utf-8
import paho.mqtt.client as mqtt
import time
import json
import commands, os, subprocess
import threading
import docker

from utilslib.getDeviceInfo import get_groupid
from utilslib.getDeviceInfo import get_deviceid, get_current_groupid, check_groupid_changed
from utilslib.getDeviceInfo import deviceId
from utilslib.save2gst import sendMessage2Group
from utilslib.clean_droped_data import clean_droped_embedding
from utilslib.uploadFile import get_qsize
import utilslib.aliyunUpload

from threading import Timer

import classifier_rest_client as classifier

DEBUG_ON=False
#HOST='127.0.0.1'
#PORT='1883'
HOST='mq.tiegushi.com'
PORT='8080'
TRANSPORT='tcp'
#PORT='80'
#TRANSPORT='websocket'
CLEAR_FLAG=False

def json_load_byteified(file_handle):
    return _byteify(
        json.load(file_handle, object_hook=_byteify),
        ignore_dicts=True
    )

def json_loads_byteified(json_text):
    return _byteify(
        json.loads(json_text, object_hook=_byteify),
        ignore_dicts=True
    )

def _byteify(data, ignore_dicts = False):
    # if this is a unicode string, return its string representation
    if isinstance(data, unicode):
        return data.encode('utf-8')
    # if this is a list of values, return list of byteified values
    if isinstance(data, list):
        return [ _byteify(item, ignore_dicts=True) for item in data ]
    # if this is a dictionary, return dictionary of byteified keys and values
    # but only if we haven't already byteified it
    if isinstance(data, dict) and not ignore_dicts:
        return {
            _byteify(key, ignore_dicts=True): _byteify(value, ignore_dicts=True)
            for key, value in data.iteritems()
        }
    # if it's anything else, return it in its original form
    return data

def installncftpThreadFunc(device_id='', toid=''):
    try:
        if len(device_id) > 1 and len(toid) > 1:
            sendMessage2Group(device_id, toid, 'Received installncftp command, doing...')
        # out_put = subprocess.check_output(['apt-get', 'update'])
        # print("installncftpThreadFunc: apt-get update")

        if "sharpai.log" in os.listdir(os.path.abspath(os.path.join(os.getenv('RUNTIME_BASEDIR', os.path.join(os.path.dirname(__file__),os.path.pardir)), os.path.pardir))):
            out_put = subprocess.check_output(['apt-get', 'install', "-y", 'lftp'])
            print("installncftpThreadFunc: install lftp result is {}".format(out_put))
        else:
            out_put = subprocess.check_output(['apt-get', 'install', "-y", 'ncftp'])
            print("installncftpThreadFunc: install ncftpput result is {}".format(out_put))
        if len(device_id) > 1 and len(toid) > 1:
            sendMessage2Group(device_id, toid, 'install tools suc {}, {}'.format(out_put, device_id))
    except OSError as e:
        print "installncftpThreadFunc Error: "
        print(e)
        if len(device_id) > 1 and len(toid) > 1:
            sendMessage2Group(device_id, toid, 'install tools error: {}, {}'.format(e, device_id))
    return

def uploadLogsThreadFunc(device_id='', toid=''):
    if len(device_id) > 1 and len(toid) > 1:
        sendMessage2Group(device_id, toid, 'Received uploadlogs command, doing...')

    IS_RK3288 = False
    if "sharpai.log" in os.listdir(os.path.abspath(os.path.join(os.getenv('RUNTIME_BASEDIR', os.path.join(os.path.dirname(__file__),os.path.pardir)), os.path.pardir))):
        IS_RK3288 = True
    print("IS_RK3288 {}".format(IS_RK3288))

    if IS_RK3288:
        BASEPATH = os.path.join(os.getenv('RUNTIME_BASEDIR', "/data/data/com.termux/files/home/runtime"), os.path.pardir)
    else:
        BASEPATH = os.path.abspath(os.path.join(os.getenv('RUNTIME_BASEDIR',os.path.join(os.path.dirname(__file__),os.path.pardir))))

    device_id = get_deviceid()
    log_dir = os.path.join(BASEPATH, 'docker_logs')
    timestamp = int(round(time.time() * 1000))
    tar_log_file_path = os.path.join(BASEPATH,  str(timestamp) + "_" + device_id + "_logs.tar.bz2")
    print("log_dir: {}".format(log_dir))
    print("tar file: {}".format(tar_log_file_path))
    try:
        out_put = subprocess.check_output(['rm', '-rf', log_dir])
        out_put = subprocess.check_output(['mkdir', log_dir])
    except OSError as e:
        print "uploadLogThreadFunc Error: "
        print(e)
        if len(device_id) > 1 and len(toid) > 1:
            sendMessage2Group(device_id, toid, 'Upload log catch error: {}, {}'.format(e, device_id))
        return

    if IS_RK3288:
        try:
            out_put = subprocess.check_output(['cp', os.path.join(BASEPATH, "sharpai.log"), log_dir])
            out_put = subprocess.check_output(['tar', '-cjf', tar_log_file_path, log_dir])
            print("uploadLogThreadFunc: tar result is {}".format(out_put))
            print("uploadLogThreadFunc: lftp uploading...")

            upload_str = "lftp -c 'put " + tar_log_file_path + " -o ftp://swftp2:swftp2@sengftp2.actiontec.com/space4sw/frank/'"
            out_put = subprocess.check_output(upload_str, shell=True)
            print("uploadLogThreadFunc: lftp upload result is {}".format(out_put))

            # out_put = subprocess.check_output(['rm', '-rf', tar_log_file_path, log_dir])
            if len(device_id) > 1 and len(toid) > 1:
                sendMessage2Group(device_id, toid, 'Upload log done: {}, {}'.format(out_put, device_id))
        except Exception as e:
            print "uploadLogThreadFunc Error: "
            print(e)
            if len(device_id) > 1 and len(toid) > 1:
                sendMessage2Group(device_id, toid, 'Upload log catch error: {}, {}'.format(e, device_id))
        finally:
            out_put = subprocess.check_output(['rm', '-rf', tar_log_file_path, log_dir])
            print("delete {}, {}".format(tar_log_file_path, log_dir))
        return

    try:
        client = docker.DockerClient(base_url='unix://var/run/docker.sock', timeout=10)
        lists = client.containers.list(all=True)
        for i in range(len(lists)):
            container = lists[i]
            log = container.logs(tail=10000)
            log_file = open(os.path.join(log_dir, container.id + '.log'), "w")
            log_file.write(log)
            log_file.close()
        out_put = subprocess.check_output(['tar', '-cjf', tar_log_file_path, log_dir])
        print("uploadLogThreadFunc: tar result is {}".format(out_put))
        print("uploadLogThreadFunc: ncftpput uploading...")
        print(os.path.exists(tar_log_file_path))
        out_put = subprocess.check_output(['ncftpput', '-u', 'swftp2', '-p', 'swftp2', '-m', '-R', '-z', 'sengftp2.actiontec.com', 'space4sw/frank/', tar_log_file_path])
        print("uploadLogThreadFunc: ncftpput result is {}".format(out_put))
        # out_put = subprocess.check_output(['rm', '-rf', tar_log_file_path, log_dir])
        if len(device_id) > 1 and len(toid) > 1:
            sendMessage2Group(device_id, toid, 'Upload log done: {}, {}'.format(out_put, device_id))
    except Exception as e:
        print "uploadLogThreadFunc Error: "
        print(e)
        if len(device_id) > 1 and len(toid) > 1:
            sendMessage2Group(device_id, toid, 'Upload log catch error: {}, {}'.format(e, device_id))
    finally:
        out_put = subprocess.check_output(['rm', '-rf', tar_log_file_path, log_dir])
        print("delete {}, {}".format(tar_log_file_path, log_dir))
    return

def uploadTrainThreadFunc(device_id='', toid=''):
    if len(device_id) > 1 and len(toid) > 1:
        sendMessage2Group(device_id, toid, 'Received uploadtraindata command, doing...')
    IS_RK3288 = False
    if "sharpai.log" in os.listdir(os.path.abspath(os.path.join(os.getenv('RUNTIME_BASEDIR', os.path.join(os.path.dirname(__file__),os.path.pardir)), os.path.pardir))):
        IS_RK3288 = True
    print("IS_RK3288 {}".format(IS_RK3288))
    BASEPATH = os.path.abspath(os.path.join(os.getenv('RUNTIME_BASEDIR',os.path.join(os.path.dirname(__file__),os.path.pardir))))
    device_id = get_deviceid()
    current_groupid = get_current_groupid()
    group_file_path = os.path.join(BASEPATH, 'data', 'faces', current_groupid)
    tar_group_file_path = group_file_path + "_" + device_id + "_train.tar.bz2"
    try:
        out_put = subprocess.check_output(['rm', '-f', tar_group_file_path])
        print("uploadTrainThreadFunc: tar -cjf {} {}".format(tar_group_file_path, group_file_path))
        out_put = subprocess.check_output(['tar', '-cjf', tar_group_file_path, group_file_path])
        print("uploadTrainThreadFunc: tar result is {}".format(out_put))
        if IS_RK3288:
            print("uploadLogThreadFunc: lftp uploading...")
            upload_str = "lftp -c 'put " + tar_group_file_path + " -o ftp://swftp2:swftp2@sengftp2.actiontec.com/space4sw/frank/'"
            out_put = subprocess.check_output(upload_str, shell=True)
            print("uploadLogThreadFunc: lftp upload result is {}".format(out_put))
        else:
            print("uploadTrainThreadFunc: ncftpput uploading...")
            out_put = subprocess.check_output(['ncftpput', '-u', 'swftp2', '-p', 'swftp2', '-m', '-R', '-z', 'sengftp2.actiontec.com', 'space4sw/frank/', tar_group_file_path])
            print("uploadTrainThreadFunc: ncftpput result is {}".format(out_put))
        if len(device_id) > 1 and len(toid) > 1:
            sendMessage2Group(device_id, toid, 'Upload train data done: {}, {}, {}'.format(out_put, current_groupid, device_id))
    except OSError as e:
        print "uploadTrainThreadFunc Error: "
        print(e)
        if len(device_id) > 1 and len(toid) > 1:
            sendMessage2Group(device_id, toid, 'Upload train catch error: {}, {}'.format(e, device_id))
    return

def uploadTestThreadFunc(device_id='', toid=''):
    if len(device_id) > 1 and len(toid) > 1:
        sendMessage2Group(device_id, toid, 'Received uploadtestdata command, doing...')
    IS_RK3288 = False
    if "sharpai.log" in os.listdir(os.path.abspath(os.path.join(os.getenv('RUNTIME_BASEDIR', os.path.join(os.path.dirname(__file__),os.path.pardir)), os.path.pardir))):
        IS_RK3288 = True
    print("IS_RK3288 {}".format(IS_RK3288))
    BASEPATH = os.path.abspath(os.path.join(os.getenv('RUNTIME_BASEDIR',os.path.join(os.path.dirname(__file__),os.path.pardir))))
    device_id = get_deviceid()
    current_groupid = get_current_groupid()
    group_file_path = os.path.join(BASEPATH, 'data', 'face_testdataset', current_groupid)
    tar_group_file_path = group_file_path + "_" + device_id + "_test.tar.bz2"
    try:
        out_put = subprocess.check_output(['rm', '-f', tar_group_file_path])
        print("uploadTestThreadFunc: tar -cjf {} {}".format(tar_group_file_path, group_file_path))
        out_put = subprocess.check_output(['tar', '-cjf', tar_group_file_path, group_file_path])
        print("uploadTestThreadFunc: tar result is {}".format(out_put))
        if IS_RK3288:
            print("uploadLogThreadFunc: lftp uploading...")
            upload_str = "lftp -c 'put " + tar_group_file_path + " -o ftp://swftp2:swftp2@sengftp2.actiontec.com/space4sw/frank/'"
            out_put = subprocess.check_output(upload_str, shell=True)
            print("uploadLogThreadFunc: lftp upload result is {}".format(out_put))
        else:
            print("uploadTestThreadFunc: ncftpput uploading...")
            out_put = subprocess.check_output(['ncftpput', '-u', 'swftp2', '-p', 'swftp2', '-m', '-R', '-z', 'sengftp2.actiontec.com', 'space4sw/frank/', tar_group_file_path])
            print("uploadTestThreadFunc: ncftpput result is {}".format(out_put))
        if len(device_id) > 1 and len(toid) > 1:
            sendMessage2Group(device_id, toid, 'Upload test data done: {}, {}, {}'.format(out_put, current_groupid, device_id))
    except OSError as e:
        print "uploadTestThreadFunc Error: "
        print(e)
        if len(device_id) > 1 and len(toid) > 1:
            sendMessage2Group(device_id, toid, 'Upload test catch error: {}, {}'.format(e, device_id))
    return

def syncDatasetsThreadFunc(device_id='', toid=''):
    try:
        if len(device_id) > 1 and len(toid) > 1:
            sendMessage2Group(device_id, toid, 'Received syncdatasets command, doing...')
        app_name = ''
        if os.path.exists('utilslib/syn_data.exe'):
            app_name = 'syn_data.exe'
        elif os.path.exists('utilslib/syn_data.py'):
            app_name = 'syn_data.py'
        else:
            if len(device_id) > 1 and len(toid) > 1:
                sendMessage2Group(device_id, toid, 'syncDatasetsThreadFunc: no syn_data.exe or syn_data.py {}'.format(device_id))
            return
        current_groupid = get_current_groupid()
        BASEPATH = os.path.abspath(os.path.join(os.getenv('RUNTIME_BASEDIR',os.path.join(os.path.dirname(__file__),os.path.pardir))))
        cmd = "export PYTHONPATH={} && cd {} && python utilslib/{}".format(BASEPATH, BASEPATH, app_name)
        print("syncDatasetsThreadFunc: exec command: {}".format(cmd))
        if len(device_id) > 1 and len(toid) > 1:
            sendMessage2Group(device_id, toid, 'Execute command: {}, {}'.format(cmd, device_id))
        out_put = subprocess.check_output(cmd+";exit 0", shell=True)
        if len(device_id) > 1 and len(toid) > 1:
            sendMessage2Group(device_id, toid, 'Execute syncDatasetsThreadFunc command completely, {}, {} {}'.format(out_put, current_groupid, device_id))
    except OSError as e:
        print "syncDatasetsThreadFunc Error: "
        print(e)
        if len(device_id) > 1 and len(toid) > 1:
            sendMessage2Group(device_id, toid, 'syncDatasetsThreadFunc catch error: {}'.format(e))
    return

def syncFacesDatasetsThreadFunc(device_id='', toid=''):
    try:
        if len(device_id) > 1 and len(toid) > 1:
            sendMessage2Group(device_id, toid, 'Received syncfacesdatasets command, doing...')
        app_name = ''
        if os.path.exists('utilslib/sync_facesdata.exe'):
            app_name = 'sync_facesdata.exe'
        elif os.path.exists('utilslib/sync_facesdata.py'):
            app_name = 'sync_facesdata.py'
        else:
            if len(device_id) > 1 and len(toid) > 1:
                sendMessage2Group(device_id, toid, 'syncFacesDatasetsThreadFunc: no sync_facesdata.exe or sync_facesdata.py {}'.format(device_id))
            return
        current_groupid = get_current_groupid()
        BASEPATH = os.path.abspath(os.path.join(os.getenv('RUNTIME_BASEDIR',os.path.join(os.path.dirname(__file__),os.path.pardir))))
        cmd = "export PYTHONPATH={} && cd {} && python utilslib/{}".format(BASEPATH, BASEPATH, app_name)
        print("syncDatasetsThreadFunc: exec command: {}".format(cmd))
        if len(device_id) > 1 and len(toid) > 1:
            sendMessage2Group(device_id, toid, 'Execute command: {}, {}'.format(cmd, device_id))
        out_put = subprocess.check_output(cmd+";exit 0", shell=True)
        if len(device_id) > 1 and len(toid) > 1:
            sendMessage2Group(device_id, toid, 'Execute syncFacesDatasetsThreadFunc command completely, {}, {} {}'.format(out_put, current_groupid, device_id))
    except OSError as e:
        print "syncDatasetsThreadFunc Error: "
        print(e)
        if len(device_id) > 1 and len(toid) > 1:
            sendMessage2Group(device_id, toid, 'syncFacesDatasetsThreadFunc catch error: {}, {}'.format(e, device_id))
    return

def checkTrainsetThreadFunc(device_id='', toid=''):
    try:
        current_groupid = get_current_groupid()
        BASEPATH = os.path.abspath(os.path.join(os.getenv('RUNTIME_BASEDIR',os.path.join(os.path.dirname(__file__),os.path.pardir))))
        cmd = "diff -r -x face_embedding {}/data/faces/{} {}/data/faces/{}_sync/".format(BASEPATH, current_groupid, BASEPATH, current_groupid)
        print("checkTrainsetThreadFunc: exec command: {}".format(cmd))
        if len(device_id) > 1 and len(toid) > 1:
            sendMessage2Group(device_id, toid, 'Execute command: {}, {}'.format(cmd, device_id))
        out_put = subprocess.check_output(cmd+";exit 0", shell=True)
        if len(device_id) > 1 and len(toid) > 1:
            sendMessage2Group(device_id, toid, 'Execute checkTrainsetThreadFunc command completely: {}, {}'.format(out_put, device_id))
    except OSError as e:
        print "checkTrainsetThreadFunc Error: "
        print(e)
        if len(device_id) > 1 and len(toid) > 1:
            sendMessage2Group(device_id, toid, 'checkTrainsetThreadFunc catch error: {}, {}'.format(e, device_id))
    return

def finalSyncDatasetsThreadFunc(self=None, device_id='', toid=''):
    try:
        if len(device_id) > 1 and len(toid) > 1:
            sendMessage2Group(device_id, toid, 'Received finalsyncdatasets command, doing...')
        if self and self.disposeFinalSyncDatasetsThreadFunc:
            self.disposeFinalSyncDatasetsThreadFunc(device_id, toid)
        if len(device_id) > 1 and len(toid) > 1:
            sendMessage2Group(device_id, toid, 'Execute finalsyncdatasets command completely, {}'.format(device_id))
    except OSError as e:
        print "syncDatasetsThreadFunc Error: "
        print(e)
        if len(device_id) > 1 and len(toid) > 1:
            sendMessage2Group(device_id, toid, 'syncDatasetsThreadFunc catch error: {}'.format(e))
    return

def syncStatusInfoThreadFunc(self=None, device_id='', toid=''):
    try:
        if len(device_id) > 1 and len(toid) > 1:
            sendMessage2Group(device_id, toid, 'Received syncstatusinfo command, doing...')
        if self and self.disposeSyncStatusInfoThreadFunc:
            self.disposeSyncStatusInfoThreadFunc(device_id, toid)
        current_groupid = get_current_groupid()
        if len(device_id) > 1 and len(toid) > 1:
            sendMessage2Group(device_id, toid, 'Execute syncstatusinfo command completely, {} {}'.format(current_groupid, device_id))
    except OSError as e:
        print "syncDatasetsThreadFunc Error: "
        print(e)
        if len(device_id) > 1 and len(toid) > 1:
            sendMessage2Group(device_id, toid, 'syncstatusinfo catch error: {}'.format(e))
    return

def getUploadQueueInfoThreadFunc(self=None, device_id='', toid=''):
    try:
        if len(device_id) > 1 and len(toid) > 1:
            # sendMessage2Group(device_id, toid, 'Received getUploadQueueInfoThreadFunc command, doing...{}'.format(utilslib.aliyunUpload.total_time))
            sendMessage2Group(device_id, toid, 'Upload queue remaining tasks: {}, succeed: {}, failed: {}, avg_time: {}'.format(get_qsize(), utilslib.aliyunUpload.success_count, utilslib.aliyunUpload.error_count, 0 if utilslib.aliyunUpload.success_count == 0 else "%.2f"%(utilslib.aliyunUpload.total_time/utilslib.aliyunUpload.success_count)))
    except Exception as e:
        print "trainThreadFunc Error: "
        print(e)
        if len(device_id) > 1 and len(toid) > 1:
            sendMessage2Group(device_id, toid, 'getUploadQueueInfoThreadFunc catch error: {}'.format(e))
    return

def trainThreadFunc(self=None, device_id='', toid=''):

    BASEPATH = os.path.abspath(os.path.join(os.getenv('RUNTIME_BASEDIR',os.path.join(os.path.dirname(__file__),os.path.pardir))))
    if DEBUG_ON:
        print('in train thread, device_id {}, toid {}'.format(device_id,toid))
    try:
        if len(device_id) > 1 and len(toid) > 1:
            sendMessage2Group(device_id, toid, 'Received trainThreadFunc command, doing...')
        else:
            print('id is not enough device_id %s,toid %s',device_id,toid)
        current_groupid = get_current_groupid()
        if DEBUG_ON:
            print('current group id {}'.format(current_groupid))
        clean_droped_embedding(current_groupid)
        svm_current_groupid_basepath = os.path.join(BASEPATH, 'data', 'faces', current_groupid)
        if DEBUG_ON:
            print('svm_current_groupid_basepath {}'.format(svm_current_groupid_basepath))
        # for style in ['left_side', 'right_side', 'front']:
        for style in ['front']:
            svm_train_dataset = os.path.join(svm_current_groupid_basepath, style, 'face_dataset')
            if not os.path.exists(svm_train_dataset):
                print('not os.path.exists({}})'.format(svm_train_dataset))
                continue
            svn_train_pkl = os.path.join(svm_current_groupid_basepath, style, 'classifier_182.pkl')
            args_list = ['TRAIN', svm_train_dataset, 'facenet_models/20170512-110547/20170512-110547.pb',
                         svn_train_pkl, '--batch_size', '1000']

            device_id = get_deviceid()
            if DEBUG_ON:
                print('device_id is {}'.format(device_id))
            if self and self.generate_embedding_ifmissing:
                self.generate_embedding_ifmissing(svm_train_dataset)
            stime = time.time()
            print('Before train.')
            ret_val = classifier.train_svm_with_embedding(args_list)
            print('After train.')
            message = "Failed"
            if ret_val is None:
                message = "Failed"
            else:
                if ret_val is "OK":
                    train_cost = round(time.time() - stime, 2)
                    message = 'Training done in {}s'.format(train_cost)
                else:
                    message = ret_val
            print('-> Train SVM cost {}s'.format(time.time() - stime))

            if len(device_id) > 1 and len(toid) > 1:
                #sendMessage2Group(device_id, toid, '-> Train cost {}s'.format(time.time() - stime))
                sendMessage2Group(device_id, toid, message)
    except OSError as e:
        print "trainThreadFunc Error: "
        print(e)
        if len(device_id) > 1 and len(toid) > 1:
            sendMessage2Group(device_id, toid, 'trainThreadFunc catch error: {}'.format(e))
    except:
        print('exception in trainThreadFunc')
    return

def groupchangedThreadFunc(self=None, device_id='', toid=''):
    try:
        if len(device_id) > 1 and len(toid) > 1:
            sendMessage2Group(device_id, toid, 'Received groupchangedThreadFunc command, doing...')
        check_groupid_changed()
        self.reSubscribeGroup(device_id)
        current_groupid = get_current_groupid()
        print('groupchangedThreadFunc current_groupid = {}'.format(current_groupid))
    except OSError as e:
        print "trainThreadFunc Error: "
        print(e)
        if len(device_id) > 1 and len(toid) > 1:
            sendMessage2Group(device_id, toid, 'groupchangedThreadFunc catch error: {}'.format(e))
    return

def do_updateThreadFunc(self=None, device_id='', toid=''):
    try:
        app_name = ''
        if os.path.exists('/data/do_update'):
            app_name = 'do_update'
        elif os.path.exists('/data/do_update.sh'):
            app_name = 'do_update.sh'
        else:
            if len(device_id) > 1 and len(toid) > 1:
                sendMessage2Group(device_id, toid, 'do_updateThreadFunc: no /data/do_update or /data/do_update.sh {}'.format(device_id))
            return

        cmd = "/data/{}".format(app_name)
        print("do_updateThreadFunc: exec command: {}".format(cmd))
        if len(device_id) > 1 and len(toid) > 1:
            sendMessage2Group(device_id, toid, 'Execute command: {}, {}'.format(cmd, device_id))
        out_put = subprocess.check_output(cmd+";exit 0", shell=True)
        if len(device_id) > 1 and len(toid) > 1:
            current_groupid = get_current_groupid()
            sendMessage2Group(device_id, toid, 'Execute do_updateThreadFunc command completely, {}, {} {}'.format(out_put, current_groupid, device_id))
    except OSError as e:
        print "do_updateThreadFunc Error: "
        print(e)
        if len(device_id) > 1 and len(toid) > 1:
            sendMessage2Group(device_id, toid, 'do_updateThreadFunc catch error: {}, {}'.format(e, device_id))
    return

def get_version_from_file():
    vfile='version.txt'
    needupdate=''

    if os.path.exists('/data/needupdate'):
        needupdate='.'

    try:
        with open(vfile, 'r') as group_id_file:
            version=group_id_file.read().replace('\n', '')
    except IOError:
        return 'null'
    if version is not None and version != '':
        version = version + needupdate
        return version
    return 'null'

def devices_group_message(msg_payload, handle, handle2):
    data = json.loads(msg_payload)
    group_id  = data.get("group_id")
    msg_type  = data.get("type")
    url       = data.get("url")
    device_id = data.get("device_id", '')
    face_id   = data.get("face_id", '')
    drop      = data.get("drop")
    #img_type  = data.get("img_type", 'face')  # 测试用，默认face
    img_type  = data.get("img_type")
    sqlid     = data.get("sqlid")
    style     = data.get('style')
    rm_reason = data.get("rm_reson", '')
    drop_person = data.get("drop_person", '')

    if rm_reason.encode('utf-8') == "非人脸":
        rm_reason = "notface"
        face_id = "notface"
    else:
        rm_reason = 'other notface'

    if (drop_person == 'true') or (drop_person == "True") or (drop_person == True):
        if group_id and face_id:
            if handle2 is not None:
                handle2(group_id=group_id, face_id=face_id, drop_person=drop_person)
                return


    if (group_id is not None) and (msg_type is not None):
        if (msg_type == "trainset"):
            if (url is not None) and (face_id is not None) and (drop is not None):
                if handle is not None:
                    handle(url=url, objId=face_id, group_id=group_id, device_id=device_id,
                           drop=drop, img_type=img_type, sqlId=sqlid, style=style, img_ts=0, rm_reason=rm_reason)
                    #print("updateDataSet()")
            else:
                print("bad args to updateDataSet")
    return

class MyMQTTClass:
    def __init__(self, clientid=None):
        self._client_id = clientid
        self._mqttc = None
        self._topics=[]
        self._topics_group=[]
        self._topics_group_cmd=[]
        self.UpateTrainsetHandle = None
        self.dropPersonHandle = None
        self.mqttDebugOnOff = None
        self.disposeFinalSyncDatasetsThreadFunc = None
        self.disposeSyncStatusInfoThreadFunc = None
        self.generate_embedding_ifmissing = None
        self.installncftpThread = None
        self.uploadTrainThread = None
        self.uploadLogsThread = None
        self.uploadTestThread = None
        self.syncDatasetsThread = None
        self.syncFacesDatasetsThread = None
        self.checkTrainsetThread = None
        self.finalSyncDatasetsThread = None
        self.syncStatusInfoThread = None
        self.do_updateThread = None
        self.trainThread = None
        self.getUploadInfoThread = None
        self.groupchangedThread = None
        self.mqttMsgIds = {}#OrderedDict()
        self.photosCount = 0
        self._selftopic = None
        self.autoSyncTimer = None
        self.autoSyncTrain = None
        device_id = get_deviceid()
        if device_id is not None and len(device_id) > 1:
            self._selftopic = "/msg/d/{}".format(device_id)

    def setAutoTrainTimeout(self):
        toid = get_current_groupid()
        device_id = get_deviceid()
        if device_id is not None and toid is not None and len(device_id) > 1 and len(toid) > 1:
            sendMessage2Group(device_id, toid, 'train')
        else:
            print("setAutoTrainTimeout: get device_id or toid failed!")

    def setSyncTimeout(self):
        toid = get_current_groupid()
        device_id = get_deviceid()
        if device_id is not None and toid is not None and len(device_id) > 1 and len(toid) > 1:
            sendMessage2Group(device_id, toid, "finalsyncdatasets")
        else:
            print("setSyncTimeout: get device_id or toid failed!")
        if self.autoSyncTimer:
            self.autoSyncTimer.cancel()
            self.autoSyncTimer = None
        self.autoSyncTimer = Timer(3600, self.setSyncTimeout)
        self.autoSyncTimer.start()
        self.autoSyncTrain = Timer(1800, self.setAutoTrainTimeout)
        self.autoSyncTrain.start()
        return

    def clearSyncTimeout(self):
        if self.autoSyncTimer:
            self.autoSyncTimer.cancel()
            self.autoSyncTimer = None
        if self.autoSyncTrain:
            self.autoSyncTrain.cancel()
            self.autoSyncTrain = None


    def train_svm(self, device_id, toid, msg):
        if self.trainThread!=None and self.trainThread.is_alive():
            print('trainThread still running.')
            if len(device_id) > 1 and len(toid) > 1:
                sendMessage2Group(device_id, toid, msg)
            return
        else:
            print('trainThread is not running. Start it...')
        self.trainThread = threading.Thread(target=trainThreadFunc, kwargs={'self':self, 'device_id':device_id, 'toid':toid})
        self.trainThread.daemon = True
        self.trainThread.start()
        return

    def reSubscribeGroup(self, uuid):
        if DEBUG_ON:
            print("mqtt reSubscribeGroup, uuid: " + str(uuid))

        groupid, group_cmd = get_groupid(uuid)
        new_topics = []
        new_topics_cmd = []
        for i in range(len(groupid)):
            if len(groupid[i])>0:
                new_topics.append(groupid[i])

        for i in range(len(group_cmd)):
            if len(group_cmd[i])>0:
                new_topics_cmd.append(group_cmd[i])

        if len(new_topics) > 0:
            for i in range(len(self._topics_group)):
                if len(self._topics_group[i])>0:
                    self._mqttc.unsubscribe(self._topics_group[i])
            for i in range(len(self._topics_group_cmd)):
                if len(self._topics_group_cmd[i])>0:
                    self._mqttc.unsubscribe(self._topics_group_cmd[i])
            for i in range(len(new_topics)):
                if len(new_topics[i])>0:
                    self._mqttc.subscribe(new_topics[i], qos=1)
            for i in range(len(new_topics_cmd)):
                if len(new_topics_cmd[i])>0:
                    self._mqttc.subscribe(new_topics_cmd[i], qos=1)
            del self._topics_group
            del self._topics_group_cmd
            self._topics_group = new_topics
            self._topics_group_cmd = new_topics_cmd
            print(self._topics_group)
            print(self._topics_group_cmd)

    def mqtt_on_connect(self, mqttc, obj, flags, rc):
        #if DEBUG_ON:
        print("mqtt connected, rc: " + str(rc))
        self.setSyncTimeout()

        if rc is 0:
            for i in range(len(self._topics)):
                if len(self._topics[i])>0:
                    self._mqttc.subscribe(self._topics[i], qos=1)
                    print(self._topics[i])

            for i in range(len(self._topics_group)):
                if len(self._topics_group[i])>0:
                    self._mqttc.subscribe(self._topics_group[i], qos=1)
                    print(self._topics_group[i])


            for i in range(len(self._topics_group_cmd)):
                if len(self._topics_group_cmd[i])>0:
                    self._mqttc.subscribe(self._topics_group_cmd[i], qos=1)
                    print(self._topics_group_cmd[i])
            #self._mqttc.subscribe('trainset', qos=1)
            #self._mqttc.subscribe('workaicmd', qos=1)

    def mqtt_on_message(self, mqttc, obj, msg):
        #if DEBUG_ON:
        #print "on message: topic=%s qos=%d payload=%s" % (msg.topic, msg.qos, msg.payload)

        load_text = json.loads(msg.payload)
        text = load_text.get('text', '')
        if text == 'groupchanged':
            device_id = get_deviceid()
            toid = ''
            if self.groupchangedThread!=None and self.groupchangedThread.is_alive():
                print('groupchangedThread still running.')
                if len(device_id) > 1 and len(toid) > 1:
                    sendMessage2Group(device_id, toid, 'groupchangedThread still running')
                return
            else:
                print('groupchangedThread is not running. Start it...')
            self.groupchangedThread = threading.Thread(target=groupchangedThreadFunc, kwargs={'self':self, 'device_id':device_id, 'toid':toid})
            self.groupchangedThread.daemon = True
            self.groupchangedThread.start()
            return
        #group message
        for i in range(len(self._topics_group)):
            if msg.topic == self._topics_group[i]:
                devices_group_message(msg.payload, self.UpateTrainsetHandle, self.dropPersonHandle)
                break

        #group cmd message
        for i in range(len(self._topics_group_cmd)):
            if msg.topic == self._topics_group_cmd[i]:
                #TODO:这里判断是不是要训练

                toid = ''
                device_id = get_deviceid()
                #print(msg.topic)
                #print(msg.payload)
                #load_text = json.loads(msg.payload)
                load_text = json_loads_byteified(msg.payload)

                msgId = load_text.get('_id', '')
                if msgId is None or msgId is '':
                    if len(device_id) > 1 and len(toid) > 1:
                        sendMessage2Group(device_id, toid, "Missing msgId in message!")
                    return
                if msgId in self.mqttMsgIds and self.mqttMsgIds[msgId] == 1:
                    print "Duplicate message, dismiss it: topic=%s qos=%d payload=%s" % (msg.topic, msg.qos, msg.payload)
                    return
                self.mqttMsgIds[msgId] = 1
                #if len(self.mqttMsgIds) > 1000:

                text = load_text.get('text', '')
                if text is not None or text is not '':
                    to = load_text.get('to', '')
                    if to is not None or to is not '':
                        toid = to.get('id', '')
                if text == 'ping':
                    device_id = get_deviceid()
                    if len(device_id) > 1 and len(toid) > 1:
                        #sendMessage2Group(device_id, toid, '-> Train cost {}s'.format(time.time() - stime))
                        sendMessage2Group(device_id, toid, 'pong ' + get_version_from_file())
                    return
                if text == 'debug on' or text == 'Debug on':
                    if self.mqttDebugOnOff is not None:
                        self.mqttDebugOnOff(True)
                    return
                if text == 'debug off' or text == 'Debug off':
                    if self.mqttDebugOnOff is not None:
                        self.mqttDebugOnOff(False)
                    return
        	if text == "queryqueue":
        	    if self.getUploadInfoThread != None and self.getUploadInfoThread.is_alive():
        	        print('getUploadInfoThread still running')
        	        if len(device_id) > 1 and len(toid) > 1:
               	            sendMessage2Group(device_id, toid, 'getUploadInfoThread still running')
        	        return
        	    else:
                        print('getUploadInfoThread is not running. Start it...')
                    self.getUploadInfoThread = threading.Thread(target=getUploadQueueInfoThreadFunc, kwargs={'self':self, 'device_id':device_id, 'toid':toid})
                    self.getUploadInfoThread.daemon = True
                    self.getUploadInfoThread.start()
		    return
                if text == 'train':
                    if self.trainThread!=None and self.trainThread.is_alive():
                        print('trainThread still running.')
                        if len(device_id) > 1 and len(toid) > 1:
                            sendMessage2Group(device_id, toid, 'trainThread still running')
                        else:
                            print('no deviceid/groupid device_id %s,toid %s',device_id,toid)
                        return
                    else:
                        print('trainThread is not running. Start it...')
                    self.trainThread = threading.Thread(target=trainThreadFunc, kwargs={'self':self, 'device_id':device_id, 'toid':toid})
                    self.trainThread.daemon = True
                    self.trainThread.start()
                    return
                if text == 'oldtrain':
                    current_groupid = get_current_groupid()
                    clean_droped_embedding(current_groupid)
                    svm_current_groupid_basepath = os.path.join('data', 'faces', current_groupid)
                    # for style in ['left_side', 'right_side', 'front']:
                    for style in ['front']:
                        svm_train_dataset = os.path.join(svm_current_groupid_basepath, style, 'face_dataset')
                        if not os.path.exists(svm_train_dataset):
                            continue
                        svn_train_pkl = os.path.join(svm_current_groupid_basepath, style, 'classifier_182.pkl')
                        args_list = ['TRAIN', svm_train_dataset, 'facenet_models/20170512-110547/20170512-110547.pb',
                                     svn_train_pkl, '--batch_size', '1000']

                        device_id = get_deviceid()

                        if self and self.generate_embedding_ifmissing:
                            self.generate_embedding_ifmissing(svm_train_dataset)
                        stime = time.time()
                        ret_val = classifier.train_svm_with_embedding(args_list)
                        message = "Failed"
                        if ret_val is None:
                            message = "Failed"
                        else:
                            if ret_val is "OK":
                                train_cost = round(time.time() - stime,2)
                                message = 'Training done in {}s'.format(train_cost)
                            else:
                                message = ret_val
                        print('-> Train SVM cost {}s'.format(time.time() - stime))

                        if len(device_id) > 1 and len(toid) > 1:
                            #sendMessage2Group(device_id, toid, '-> Train cost {}s'.format(time.time() - stime))
                            sendMessage2Group(device_id, toid, message)
                    return
                if text == 'train2':
                    pid_list = []
                    trainning = os.popen('ps a | grep "Mobilenet\/train"')
                    for line in trainning:
                        pid_list.append(line)
                    if len(pid_list) > 0:
                        print('>>> already in trainning, ignore this train2_cmd')
                        return

                    current_groupid = get_current_groupid()
                    if os.path.exists('Mobilenet/train.exe'):
                        s = subprocess.Popen('Mobilenet/train.exe {}'.format(current_groupid), shell=True)
                    elif os.path.exists('Mobilenet/train.pyc'):
                        s = subprocess.Popen('python Mobilenet/train.pyc {}'.format(current_groupid), shell=True)
                    else:
                        s = subprocess.Popen('python Mobilenet/train.py {}'.format(current_groupid), shell=True)
                    return
                if text == 'installncftp':
                    self.installncftpThread = threading.Thread(target=installncftpThreadFunc, kwargs={'device_id':device_id, 'toid':toid})
                    #uploadTrainThread.daemon = True
                    self.installncftpThread.start()
                    return
                if text == 'uploadtraindata':
                    if self.uploadTrainThread!=None and self.uploadTrainThread.is_alive():
                        print('uploadTrainThread still running.')
                        return
                    else:
                        print('uploadTrainThread is not running. Start it...')
                    self.uploadTrainThread = threading.Thread(target=uploadTrainThreadFunc, kwargs={'device_id':device_id, 'toid':toid})
                    #uploadTrainThread.daemon = True
                    self.uploadTrainThread.start()
                    return
                if text == 'uploadlogs':
                    if self.uploadLogsThread!=None and self.uploadLogsThread.is_alive():
                        print('uploadLogsThread still running.')
                        return
                    else:
                        print('uploadLogsThread is not running. Start it...')
                    self.uploadLogsThread = threading.Thread(target=uploadLogsThreadFunc, kwargs={'device_id':device_id, 'toid':toid})
                    self.uploadLogsThread.start()
                    return
                if text == 'uploadtestdata':
                    if self.uploadTestThread!=None and self.uploadTestThread.is_alive():
                        print('uploadTestThread still running.')
                        return
                    else:
                        print('uploadTestThread is not running. Start it...')
                    self.uploadTestThread = threading.Thread(target=uploadTestThreadFunc, kwargs={'device_id':device_id, 'toid':toid})
                    #uploadTrainThread.daemon = True
                    self.uploadTestThread.start()
                    return
                if text == 'syncdatasets':
                    if self.syncDatasetsThread!=None and self.syncDatasetsThread.is_alive():
                        print('syncDatasetsThread still running.')
                        return
                    else:
                        print('syncDatasetsThread is not running. Start it...')
                    self.syncDatasetsThread = threading.Thread(target=syncDatasetsThreadFunc, kwargs={'device_id':device_id, 'toid':toid})
                    #uploadTrainThread.daemon = True
                    self.syncDatasetsThread.start()
                    return
                if text == 'syncfacesdatasets':
                    if self.syncFacesDatasetsThread!=None and self.syncFacesDatasetsThread.is_alive():
                        print('syncFacesDatasetsThread still running.')
                        return
                    else:
                        print('syncFacesDatasetsThread is not running. Start it...')
                    self.syncFacesDatasetsThread = threading.Thread(target=syncFacesDatasetsThreadFunc, kwargs={'device_id':device_id, 'toid':toid})
                    #uploadTrainThread.daemon = True
                    self.syncFacesDatasetsThread.start()
                    return
                if text == 'checktrainset':
                    if self.checkTrainsetThread!=None and self.checkTrainsetThread.is_alive():
                        print('checkTrainsetThread still running.')
                        return
                    else:
                        print('checkTrainsetThread is not running. Start it...')
                    self.checkTrainsetThread = threading.Thread(target=checkTrainsetThreadFunc, kwargs={'device_id':device_id, 'toid':toid})
                    #uploadTrainThread.daemon = True
                    self.checkTrainsetThread.start()
                    return
                if text == 'finalsyncdatasets':
                    if self.finalSyncDatasetsThread!=None and self.finalSyncDatasetsThread.is_alive():
                        print('finalSyncDatasetsThread still running.')
                        if len(device_id) > 1 and len(toid) > 1:
                            sendMessage2Group(device_id, toid, 'finalSyncDatasetsThread still running')
                        return
                    else:
                        print('finalSyncDatasetsThread is not running. Start it...')
                    self.finalSyncDatasetsThread = threading.Thread(target=finalSyncDatasetsThreadFunc, kwargs={'self':self, 'device_id':device_id, 'toid':toid})
                    self.finalSyncDatasetsThread.daemon = True
                    self.finalSyncDatasetsThread.start()
                    return
                if text == 'syncstatusinfo':
                    if self.syncStatusInfoThread!=None and self.syncStatusInfoThread.is_alive():
                        print('syncStatusInfoThread still running.')
                        if len(device_id) > 1 and len(toid) > 1:
                            sendMessage2Group(device_id, toid, 'syncStatusInfoThread still running')
                        return
                    else:
                        print('syncStatusInfoThread is not running. Start it...')
                    self.syncStatusInfoThread = threading.Thread(target=syncStatusInfoThreadFunc, kwargs={'self':self, 'device_id':device_id, 'toid':toid})
                    self.syncStatusInfoThread.daemon = True
                    self.syncStatusInfoThread.start()
                    return
                if text == 'restart_core':
                    print('restarting ...')
                    ppid = os.getpid()
                    #os.kill(ppid, 9)
                    return
                if text == 'do_update':
                    if self.do_updateThread!=None and self.do_updateThread.is_alive():
                        print('do_updateThread still running.')
                        if len(device_id) > 1 and len(toid) > 1:
                            sendMessage2Group(device_id, toid, 'do_updateThread still running')
                        return
                    else:
                        print('do_updateThread is not running. Start it...')
                    self.do_updateThread = threading.Thread(target=do_updateThreadFunc, kwargs={'self':self, 'device_id':device_id, 'toid':toid})
                    self.do_updateThread.daemon = True
                    self.do_updateThread.start()
                    return

        if msg.topic == 'autogroup_dataset':
            try:
                print("autogroup_dataset: msg.payload={}".format(msg.payload))
                data = json.loads(msg.payload.decode("utf-8-sig"))
                if self.autogroupProcessor is not None:
                    self.autogroupProcessor("dataset", data)
            except Exception as e:
                print(e)
        elif msg.topic == 'sync_autogroup_dataset':
            try:
                print("received mqtt message sync_autogroup_dataset")
                if self.autogroupProcessor is not None:
                    self.autogroupProcessor("syncdataset")
            except Exception as e:
                print(e)
        elif msg.topic == 'autogroup':
            try:
                jsonData = None
                if msg.payload:
                    jsonData = json.loads(msg.payload)
                if self.autogroupProcessor is not None:
                    self.autogroupProcessor("autogroup", jsonData)
            except Exception as e:
                print(e)
        elif msg.topic == 'workaicmd':
            try:
                data = json.loads(msg.payload)
                cmd = data.get('command')
                if cmd == 'do_update':
                    print('updateing ...')
                    if os.path.exists('/data/do_update'):
                        ret = commands.getstatusoutput('/data/do_update')
                    elif os.path.exists('/data/do_update.sh'):
                        ret = commands.getstatusoutput('/data/do_update.sh')
                    print(ret)
                elif cmd == 'restart_core':
                    print('restarting ...')
                    ppid = os.getpid()
                    os.kill(ppid, 9)
            except Exception as e:
                print(e)

    def on_disconnect(self, client, userdata, rc):
        for i in range(len(self._topics)):
            if len(self._topics[i])>0:
                self._mqttc.unsubscribe(self._topics[i])
        for i in range(len(self._topics_group)):
            if len(self._topics_group[i])>0:
                self._mqttc.unsubscribe(self._topics_group[i])
        for i in range(len(self._topics_group_cmd)):
            if len(self._topics_group_cmd[i])>0:
                self._mqttc.unsubscribe(self._topics_group_cmd[i])
        #if DEBUG_ON:
        print(time.localtime(time.time()))
        print('on_disconnect')
        if rc != 0:
            print("Unexpected disconnection.")
        self.clearSyncTimeout()

    def mqtt_on_publish(self, mqttc, obj, mid):
        if DEBUG_ON:
            print("mid: " + str(mid))

    def mqtt_on_subscribe(self, mqttc, obj, mid, granted_qos):
        if DEBUG_ON:
            print("Subscribed: " + str(mid) + " granted_qos=" + str(granted_qos))

    def mqtt_on_unsubscribe(self, mqttc, userdata, mid):
        if DEBUG_ON:
            print("unsubscribe: " + str(mid))

    def publish(self, channel, message):
        if self._mqttc:
            try:
                self._mqttc.publish(channel, message, qos=1)
            except UnicodeDecodeError:
                pass

    def groupPublish(self, message):
        if self._mqttc:
            try:
                for i in range(len(self._topics_group)):
                    if len(self._topics_group[i])>0:
                        self._mqttc.publish(self._topics_group[i], message, qos=1)
                        logs= "publish " + message + " to " + self._topics_group[i]
                        print(logs)
            except UnicodeDecodeError:
                pass

    def registerUpateTrainsetHandle(self, func):
        self.UpateTrainsetHandle = func
        return

    def registerDropPersonHandle(self, func):
        self.dropPersonHandle = func
        return
    def registerMQTTDebugOnOffHandle(self,func):
        self.mqttDebugOnOff = func
        return
    def registerMQTTSyncStatusInfoHandle(self,func):
        self.disposeSyncStatusInfoThreadFunc = func
        return
    def registerMQTTFinalSyncDatasetsHandle(self,func):
        self.disposeFinalSyncDatasetsThreadFunc = func
        return
    def registerMQTTGenerateEmbeddingIfMissingHandle(self,func):
        self.generate_embedding_ifmissing = func
        return
    def initialize(self, processor, autogroupProcessor=None):
        try:
            self.processor = processor
            self.autogroupProcessor = autogroupProcessor

            if DEBUG_ON:
                print('connect again')

            self._mqttc = mqtt.Client(client_id=self._client_id,
                            clean_session=CLEAR_FLAG, transport=TRANSPORT)

            self._mqttc.reconnect_delay_set(min_delay=6, max_delay=120)
            self._mqttc.on_message = self.mqtt_on_message
            self._mqttc.on_connect = self.mqtt_on_connect
            self._mqttc.on_subscribe = self.mqtt_on_subscribe
            self._mqttc.on_unsubscribe = self.mqtt_on_unsubscribe
            self._mqttc.on_publish = self.mqtt_on_publish
            self._mqttc.on_disconnect = self.on_disconnect

            #init topics
            deviceid = get_deviceid()
            if deviceid is not None:
                deviceId = deviceid
                groupid, group_cmd = get_groupid(deviceid)
                for i in range(len(groupid)):
                    if len(groupid[i])>0:
                        self._topics_group.append(groupid[i])
                for i in range(len(group_cmd)):
                    if len(group_cmd[i])>0:
                        self._topics_group_cmd.append(group_cmd[i])

            self._topics.append('workaicmd')
            self._topics.append('autogroup_dataset')
            self._topics.append('sync_autogroup_dataset')
            self._topics.append('autogroup')
            if self._selftopic is not None:
                self._topics.append(self._selftopic)
            print self._topics
            print self._topics_group
            print self._topics_group_cmd
            # Enable this line if you are doing the snip code, off stress
            # self._mqttc.loop_start()
        except TypeError:
            print('Connect to mqtter error')
            return
    def start(self):
        self._mqttc.connect(HOST, PORT, keepalive=30)
        self._mqttc.loop_start()

    def run(self, notuse):
        self._mqttc.connect(HOST, PORT, keepalive=60)
        while True:
            try:
                #self._mqttc.loop_forever(timeout=30.0, max_packets=100, retry_first_connection=False)
                self._mqttc.loop_forever(max_packets=1000, retry_first_connection=True)
                print('Oops disconnected ?')
                time.sleep(20)
            except UnicodeDecodeError:
                time.sleep(1)
            except Exception as e:
                print(e)
                time.sleep(10)


#def msg_processor(data):
#    print(data)
#
#if __name__ == '__main__':
#    mqttc = MyMQTTClass('myuuid')
#    mqttc.initialize(msg_processor)
#    mqttc.run('')
#    time.sleep(60)
