# coding=utf-8
import requests
import time
from utilslib.getDeviceInfo import get_current_groupid

host = 'http://workaihost.tiegushi.com/'
#host = 'http://deepeye.tiegushi.com/'
def generate_protocol_string(key, ownerid, filepath, embedding, uuid,
                DO_NOT_REPORT_TO_SERVER,
                block=True, objid="", img_type="",
                accuracy=0, fuzziness=0, sqlId="", style='', ts=0, tid="", p_ids=None, waiting = False
                ):
    print("in uploadImage block {}".format(block))

    image_ts = ts
    if float(ts) < 1:
        image_ts = int(time.time() *1000)

    url = 'http://workaiossqn.tiegushi.com/' + key

    return _generate_protocol_string(keyid=key,uuid=uuid,id=objid, url=url, position=embedding, img_type=img_type,
       accuracy=accuracy, fuzziness=fuzziness, sqlId=sqlId, style=style, img_ts=image_ts,tid=tid, p_ids=p_ids, waiting = waiting)

def _generate_protocol_string(keyid,uuid, id, url, position, img_type, accuracy=0, fuzziness=0, sqlId=0, style='', img_ts=0, tid='', p_ids=None, waiting = False):
    #gst_api_url = 'http://192.168.1.73:3000/restapi/workai'
    #workAIweb_url = 'http://192.168.1.123:3000/restapi/workai'
    gst_api_url = host + 'restapi/workai'
    workAIweb_url = 'http://aixd.raidcdn.cn/restapi/workai'
    query = ''
    event_type='warn'
    if style is not None:
        styles = style.split('|')
        for s in styles:
            if s == 'dirty' or s == 'low_pixel' or s == 'blury':
                print("save2gst: dirty or low_pixel or blurry pictures, discard it: url={}".format(url))
                return
    else:
        print("save2gst: img_type is None, what's wrong? url={}".format(url))

    current_groupid = get_current_groupid()
    if current_groupid is None:
        current_groupid = 'unknown'

    if (accuracy is not None) and (accuracy > 0):
        query = '?accuracy=' + str(accuracy)
        event_type = 'notice'
    else:
        query = '?accuracy=%20'
        event_type = 'danger'

    if (fuzziness is not None) and (fuzziness > 0):
        query = query + '&fuzziness=' + str(fuzziness)
    else:
        query = query + '&fuzziness=%20'

    gst_api_url = gst_api_url + query

    payload = {'id': id,
               'uuid': uuid,
               'group_id': current_groupid,
               'img_url': url,
               'position': position,
               'type': img_type,
               'current_ts': int(time.time()*1000),
               'accuracy': accuracy,
               'fuzziness': fuzziness,
               'sqlid': sqlId,
               'style': style,
               'tid': tid,
               'img_ts': img_ts,
               'p_ids': p_ids,
               'event_type': event_type,
               'waiting': waiting
               }
    print('result of _generate_protocol_string {}'.format(payload))
    return keyid, gst_api_url, payload
def save2gst(uuid, id, url, position, img_type, accuracy=0, fuzziness=0, sqlId=0, style='', img_ts=0, tid='', p_ids=None, waiting = False):
    #gst_api_url = 'http://192.168.1.73:3000/restapi/workai'
    #workAIweb_url = 'http://192.168.1.123:3000/restapi/workai'
    gst_api_url = host + 'restapi/workai'
    workAIweb_url = 'http://aixd.raidcdn.cn/restapi/workai'
    query = ''
    event_type='warn'

    if style is not None:
        styles = style.split('|')
        for s in styles:
            if s == 'dirty' or s == 'low_pixel' or s == 'blury':
                print("save2gst: dirty or low_pixel or blurry pictures, discard it: url={}".format(url))
                return
    else:
        print("save2gst: img_type is None, what's wrong? url={}".format(url))

    current_groupid = get_current_groupid()
    if current_groupid is None:
        current_groupid = 'unknown'

    if (accuracy is not None) and (accuracy > 0):
        query = '?accuracy=' + str(accuracy)
        event_type = 'notice'
    else:
        query = '?accuracy=%20'
        event_type = 'danger'

    if (fuzziness is not None) and (fuzziness > 0):
        query = query + '&fuzziness=' + str(fuzziness)
    else:
        query = query + '&fuzziness=%20'

    gst_api_url = gst_api_url + query

    payload = {'id': id,
               'uuid': uuid,
               'group_id': current_groupid,
               'img_url': url,
               'position': position,
               'type': img_type,
               'current_ts': int(time.time()*1000),
               'accuracy': accuracy,
               'fuzziness': fuzziness,
               'sqlid': sqlId,
               'style': style,
               'tid': tid,
               'img_ts': img_ts,
               'p_ids': p_ids,
               'event_type': event_type,
               'waiting': waiting
               }
    try:
        requests.post(gst_api_url, data=payload, timeout=4)
    except Exception as e:
        print(e)

    #if img_type == 'face' and int(accuracy*100) > 0 and fuzziness > 0:
    #    try:
    #        requests.post(workAIweb_url, data=payload, timeout=4)
    #    except Exception as e:
    #        print(e)

def sendMessage2Group(uuid, group_id, text):
    if (len(uuid) < 1) or (len(group_id) < 1) or (len(text) < 1):
        return

    gst_api_url = host + 'restapi/workai-send2group'
    #gst_api_url = 'http://192.168.1.73:3000/restapi/workai-send2group'
    payload = {'uuid': uuid,
               'group_id': group_id,
               'type': 'text',
               'is_device_traing': 'true',
               'text': text,
               'ts': int(time.time())*1000
               }
    try:
        requests.post(gst_api_url, data=payload, timeout=4)
    except Exception as e:
        print(e)


def post2gst_motion(uuid, id, mid, motion_gif_url, url, imgs_list, position, img_type, accuracy=0, fuzziness=0):
    #gst_api_url = 'http://192.168.1.73:3000/restapi/workai'
    #workAIweb_url = 'http://192.168.1.123:3000/restapi/workai'
    #motion_url = 'http://192.168.0.100/restapi/workai-motion'
    motion_url = host + 'restapi/workai-motion'

    payload = {'id': id,
               'uuid': uuid,
               'mid': mid,  # motion id
               'motion_gif': motion_gif_url,
               'img_url': url,
               'imgs': imgs_list,
               'position': position,
               'type': img_type,
               'ts': int(time.time())*1000,
               'accuracy': accuracy,
               'fuzziness': fuzziness,
               }
    print(payload)
    try:
        requests.post(motion_url, data=payload, timeout=4)
    except Exception as e:
        print(e)


def post2gst_video(payload):
    url = host + 'restapi/timeline/video/'
    try:
        requests.post(url, data=payload, timeout=4)
    except Exception as e:
        print(e)
