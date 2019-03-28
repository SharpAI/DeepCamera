# coding=utf-8

TIME_LIMIT_SAME_P = 1000*60
TIME_LIMIT_DIFF_P = 1000*2
q_faces = []
pre_faceId = None
pre_trackerId = None
pre_ts = None

def push_resultQueue(result, num_face):

    global q_faces
    global pre_faceId
    global pre_trackerId
    global pre_ts

    cur_trackerId = result['trackerId']
    cur_faceId = result['face_id']
    cur_ts = int(result['ts'])
    # check people with diff trackerIDs
    if pre_ts is None:
        pre_ts = cur_ts
    duration = cur_ts - pre_ts
    if cur_trackerId != pre_trackerId:
        if duration < TIME_LIMIT_DIFF_P and num_face <= 1:
            print("duration is too short, so same person as last one")
        elif duration < TIME_LIMIT_DIFF_P and num_face>1:
            q_faces.append(result)
            modify_pre_info(cur_faceId,cur_trackerId,cur_ts)
            return True
        else:  
            if cur_faceId == pre_faceId:
                # send alert msg again if duration > 1mins
                if duration > TIME_LIMIT_SAME_P:
                    q_faces.append(result)
                    modify_pre_info(cur_faceId,cur_trackerId,cur_ts)
                    return True
            else:
                # take this face as different one
                q_faces.append(result)
                modify_pre_info(cur_faceId,cur_trackerId,cur_ts)
                return True

    modify_pre_info(cur_faceId,cur_trackerId,cur_ts)
    return False

def get_resultQueue():
    global q_faces
  
    for index, item in enumerate(q_faces):
      print(index, item)
      if  item['drop'] is not None and item['drop'] == False:
          detected_faces.append({
              'detected': item['detected'],
              'style': item['img_style_str'],
              'image_url': item['url'], #TODO
              'face_url': item['url'],
              'face_id': item['face_id'],
              'recognized': item['recognized'],
              'labeled_name': 'todo',
              'time_stamp': item['ts'],
              'accuracy': item['face_accuracy']
          })
    # clear queue
    q_faces = []

    # return detected results
    print(detected_faces)
    return detected_faces

def modify_pre_info(id1,id2,ts):
  global pre_faceId
  global pre_ts
  global pre_trackerId
  pre_faceId = id1
  pre_trackerId = id2
  pre_ts = ts
