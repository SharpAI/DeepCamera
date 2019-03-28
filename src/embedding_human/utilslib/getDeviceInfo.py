# coding=utf-8
try:
    from urllib2 import Request, urlopen, URLError, HTTPError
except Exception as e:
    from urllib.request import Request, urlopen, URLError, HTTPError

import os
import netifaces
deviceId = None
gourpId = None

device_id_file_path = os.environ.get('DEVICE_UUID_FILEPATH','/dev/ro_serialno')
group_id_file_path= os.environ.get('DEVICE_GROUP_ID_FILEPATH','/data/usr/com.deep.workai/cache/groupid.txt')

def getUUID():
    interfaces = netifaces.interfaces()
    for interface in interfaces:
        if interface == 'wlan0':
            return netifaces.ifaddresses('wlan0')[netifaces.AF_LINK][0]['addr'].strip(":")
        if interface == 'eth0':
            return netifaces.ifaddresses('eth0')[netifaces.AF_LINK][0]['addr'].strip(":")
        if interface == 'en0':
            return netifaces.ifaddresses('en0')[netifaces.AF_LINK][0]['addr'].strip(":")
    return None

def get_deviceid():
    global deviceId
    if deviceId is not None:
        return deviceId

    if os.path.exists(device_id_file_path):
        with open(device_id_file_path) as f:
            deviceId = f.readline()

    if deviceId is None or len(deviceId)<1:
        deviceId = getUUID()
        # print('>>> no file found, use MAC as deviceId %s' %(deviceId))

    if deviceId is not None and len(deviceId) > 1:
        deviceId = deviceId.strip('\n')
        #deviceId = deviceId.upper()
        # print("get deviceId: %s" %(deviceId))

    return deviceId

def get_deviceid_old():
    return get_deviceid()

def save_groupid_to_file(group_id):
    try:
        with open(group_id_file_path, "w") as group_id_file:
            group_id_file.write(group_id)
    except IOError:
        pass
def get_groupid_from_file():
    try:
        with open(group_id_file_path, 'r') as group_id_file:
            data=group_id_file.read().replace('\n', '')
    except IOError:
        return None
    if data is not None and data != '':
        return data
    return None
def set_groupid(groupid):
    global gourpId
    gourpId = groupid
def get_groupid(uuid):
    arr=[]
    cmd_arr=[]

    if(len(uuid)<1):
        return arr, cmd_arr
    groupid = get_groupid_from_file()
    if groupid is not None:
        arr.append("/device/" + groupid)
        cmd_arr.append("/msg/g/" + groupid)
        return arr, cmd_arr
    #url="http://192.168.1.230:9000/restapi/workai-getgroupid?uuid=" + uuid
    url="http://workaihost.tiegushi.com/restapi/workai-getgroupid?uuid=" + uuid
    #url = "http://deepeye.tiegushi.com/restapi/workai-getgroupid?uuid=" + uuid
    try:
        response = urlopen(url, timeout=10)
    except HTTPError as e:
        print('HTTPError: ', e.code)
    except URLError as e:
        print('URLError: ', e.reason)
    except Exception as e:
        print('Error: ', e)
    else:
        # everything is fine
        if 200 == response.getcode():
            result = response.readline()
            groupid=result.decode().split(',')
            for i in range(len(groupid)):
                if len(groupid[i])>0:
                    arr.append("/device/" + groupid[i])
                    cmd_arr.append("/msg/g/" + groupid[i])
                    # Currently we only allow tablet to join one group.
                    save_groupid_to_file(groupid[i])
        else:
            print('response code != 200')
        return arr, cmd_arr
    return arr, cmd_arr

# print get_groupid('7YRBBDB722002717')
# print get_deviceid()


# global会有BUG
def get_deviceid2():
    return get_deviceid()
def get_current_groupid(uuid=get_deviceid()):
    groupid, _ = get_groupid(uuid)
    if groupid:
        return groupid[0].replace('/device/', '')
    else:
        return None
def check_groupid_changed():
    save_groupid_to_file('')
    get_current_groupid(get_deviceid())
