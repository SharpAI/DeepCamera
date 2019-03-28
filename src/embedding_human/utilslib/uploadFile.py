from qiniuUpload import qiniu_upload_img
from aliyunUpload import aliyun_upload_img, aliyun_upload_data
import threading, time, Queue
from uuid import uuid1

uploadQueue = Queue.Queue(maxsize=1024)
event = threading.Event()

def get_qsize():
    return uploadQueue.qsize()

useAliyun=True
#useAliyun=False

class workQueue(threading.Thread):
    def __init__(self, name, handle, cb):
        super(workQueue, self).__init__()
        self.event = event
        self.name = name
        self._jobHandle = handle
        self._jobcallback = cb

    def _process_job(self, jobHandle, cb):
        while uploadQueue.empty() is False:
            job = uploadQueue.get()
            keyid = job['key']
            url = jobHandle(keyid, job['path'], 30)
            embedding = job['embedding']
            uuid = job['uuid']
            objid = job['objid']
            img_type = job['img_type']
            donot_callback = job['DO_NOT_REPORT_TO_SERVER']
            sqlId = job['sqlid']
            style = job['style']
            ts = job['ts']
            tid = job['tid']
            p_ids = job['p_ids']
            waiting = job['waiting']
            if len(url) < 1:
                print("upload failed")
            if donot_callback is not None and donot_callback is False:
                cb(job['oid'], url, embedding, uuid, objid, img_type,
                   accuracy=job['accuracy'], fuzziness=job['fuzziness'], sqlId=sqlId, style=style, img_ts=ts,tid=tid, p_ids=p_ids, waiting = waiting)

    def run(self):
        while True:
            try:
                self.event.wait()
                print("processing job ...")
                self._process_job(self._jobHandle, self._jobcallback);
                self.event.clear()
                print("no more new job, sleep ...")
            except Exception as e:
                print("Upload img to aliyun exception: {}".format(e))

    def _awakeThread(self):
        if self.event.isSet() is False:
            self.event.set()

    def uploadImage(self, key, ownerid, filepath, embedding, uuid,
                    DO_NOT_REPORT_TO_SERVER,
                    block=True, objid="", img_type="",
                    accuracy=0, fuzziness=0, sqlId="", style='', ts=0, tid="", p_ids=None, waiting = False
                    ):
        """
        Args:
            ownerid:     id of person in current picture
            filepath:    local path of current picture
            block:       if block=False, upload with thread
        Returns:
        """
        print("in uploadImage block {}".format(block))

        image_ts = ts
        if float(ts) < 1:
            image_ts = int(time.time() *1000)

        if block == False:
            uploadQueue.put({'oid': ownerid,
                             'sqlid': sqlId,
                             'path': filepath,
                             'embedding': embedding,
                             'uuid': uuid,
                             'key': key,
                             'DO_NOT_REPORT_TO_SERVER': DO_NOT_REPORT_TO_SERVER,
                             'objid': objid,
                             'img_type': img_type,
                             'accuracy': accuracy,
                             'fuzziness': fuzziness,
                             'ts': image_ts,
                             'style': style,
                             'tid': tid,
                             'p_ids': p_ids,
                             'waiting': waiting})
            self._awakeThread();
            if useAliyun is False:
                url = 'http://workaiossqn.tiegushi.com/' + key
                return url
            else:
                url = 'http://aioss.tiegushi.com/' + key
                return url
        else:
            return self._jobHandle(key, filepath, 4);

    def uploadData(self, key, data, timeout=4):
        print(key)
        url=''
        if useAliyun is True:
            url = aliyun_upload_data(key, data, timeout)
        else:
            url = qiniu_upload_data(key, data, timeout)
        return url

def uploadFileInit(callback):
    if useAliyun is True:
        upload = workQueue('aliyun', aliyun_upload_img, callback)
    else:
        upload = workQueue('qiniu', qiniu_upload_img, callback)

    upload.setDaemon(True)
    upload.start()
    return upload
