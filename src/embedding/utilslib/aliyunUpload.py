import oss2, os
import threading
import time

lock = threading.Lock()
# lock.acquire()
# lock.release()

endpoint = 'http://oss-cn-shenzhen.aliyuncs.com'
auth = oss2.Auth('Vh0snNA4Orv3emBj', 'd7p2eNO8GuMl1GtIZ0at4wPDyED4Nz')

success_count = 0
error_count= 0
total_time = 0

def aliyun_upload_img(key, imgpath, timeout=4):
    if not os.path.exists(imgpath):
        print('ops! this image not found')
        return ''

    if key is None:
        print('ops! key is None')
        return ''

    url = 'http://aioss.tiegushi.com/' + key

    for i in range(3):
        try:
            oss2.defaults.connect_timeout=timeout
            bucket = oss2.Bucket(auth, endpoint, 'workai')

            start = time.time()
            result = bucket.put_object_from_file(key, imgpath)
            end = time.time()

            if result is not None and result.status == 200:
                print('uploaded ' + imgpath + ' as ' + url)
                os.remove(imgpath)

                global total_time
                global success_count
                lock.acquire()
                success_count += 1
                total_time += (end - start)
                lock.release()
                return url
            else:
                print("upload to aliyun failed")
        except Exception as e:
            print(e)
            print("upload to aliyun failed")

    global error_count
    lock.acquire()
    error_count += 1
    lock.release()

    return ''


def aliyun_upload_data(key, data, timeout=4):
    SUFFIX = '_embedding'
    if data == '':
        return ''
    key = key + SUFFIX
    url = 'http://aioss.tiegushi.com/' + key

    for i in range(3):
        try:
            oss2.defaults.connect_timeout=timeout
            bucket = oss2.Bucket(auth, endpoint, 'workai')
            start = time.time()
            result = bucket.put_object(key, data)
            end = time.time()
            
            if result is not None and result.status == 200:
                print('uploaded data as ' + url)

                global total_time
                global success_count
                lock.acquire()
                success_count += 1
                total_time += (end - start)
                lock.release()
                return url
            else:
                print("upload to aliyun failed")
        except Exception as e:
            print(e)
            print("upload to aliyun failed")

    global error_count
    lock.acquire()
    error_count += 1
    lock.release()

    return ''


# if __name__ == '__main__':
#    img_url = "xxx"
#    new_img_url=aliyun_upload_img('./example.jpg')
#    if (len(new_img_url)) < 1:
#        new_img_url = img_url
#    print(new_img_url)
