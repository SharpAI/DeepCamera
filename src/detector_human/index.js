
process.on('uncaughtException', function (err) {
    console.error('uncaughtException',err)
});
var Queue = require('bull');
var motion=require('./motion')
//var motion=require('./od')
var deepeye=require('./deepeye')
var waitqueue=require('./waitqueue')
var timeline=require('./timeline')
var face_motions=require('./face_motions')

rt_msg = require('./realtime_message')

var ON_DEBUG = false
var FACE_DETECTION_DURATION = 100 // MS, fixed value implement first
var TRACKER_ID_SILIENCE_INTERVAL = 4000 // MS, fixed value implement first
var MAX_UNKNOWN_FRONT_FACE_IN_TRACKING = 5 // 陌生人情况下的入队列阈值
var cameras_tracker = {}

var REDIS_HOST = process.env.REDIS_HOST || "redis"
var REDIS_PORT = process.env.REDIS_PORT || 6379

function GetEnvironmentVarInt(varname, defaultvalue)
{
    var result = process.env[varname];
    if(result!=undefined)
        return parseInt(result,10);
    else
        return defaultvalue;
}

// DEEP_ANALYSIS_MODE true=允许队列缓存, false=不允许队列缓存
var DEEP_ANALYSIS_MODE = GetEnvironmentVarInt('DEEP_ANALYSIS_MODE',1)
// SAMPLING_TO_SAVE_ENERGY_MODE true，同一个Camera在进行Embedding计算的时候其他图片不再计算Embedding, false=关闭
var SAMPLING_TO_SAVE_ENERGY_MODE = GetEnvironmentVarInt('SAMPLING_TO_SAVE_ENERGY_MODE',1)
// RESTRICT_RECOGNITON_MODE true=只做正脸识别, false=侧脸和正脸都做识别
var RESTRICT_RECOGNITON_MODE = GetEnvironmentVarInt('RESTRICT_RECOGNITON_MODE',1)
// MINIMAL_FACE_RESOLUTION 定义脸最小分辨率
var MINIMAL_FACE_RESOLUTION = GetEnvironmentVarInt('MINIMAL_FACE_RESOLUTION', 200)
// BIGGEST_FACE_ONLY_MODE 只计算最大脸模式，通常用于闸机系统，多算无意的模式，缺省关闭
var BIGGEST_FACE_ONLY_MODE = GetEnvironmentVarInt('BIGGEST_FACE_ONLY_MODE', 0)
// UPLOAD_IMAGE_SERVICE_ENABLED, true 打开minio上传监听，false 关闭minio上传监听
var UPLOAD_IMAGE_SERVICE_ENABLED = GetEnvironmentVarInt('UPLOAD_IMAGE_SERVICE_ENABLED', 0)
// GIF_UPLOADING 控制GIF图上传
var GIF_UPLOADING = GetEnvironmentVarInt('GIF_UPLOADING', 1)
// TASK_IN_DETECTOR_EXPIRE_IN_SECONDS Celery重启的时候，已经发出的任务不会超时，将导致永远不再执行
var TASK_IN_DETECTOR_EXPIRE_IN_SECONDS = GetEnvironmentVarInt('TASK_IN_DETECTOR_EXPIRE_IN_SECONDS', 15)

if(UPLOAD_IMAGE_SERVICE_ENABLED){
  var upload_listener=require('./upload_listener')
}

// Use database 22 to void confict if there's one
var gifQueue = new Queue('gif making worker', {redis: {
  host: REDIS_HOST,
  port: REDIS_PORT,
  db: 2
}});
/*
var memwatch = require('memwatch-next')

memwatch.on('leak', (info) => {
  console.error('Memory leak detected:\n', info)
})
*/

/*
    {"BHcGSzII9G":{
                   "tracker_id_alive_ts":1522130633840,
                   "current_tracker_id":1522130630574,
                   "current_person_count":1,
                   "old_ts":1522130633840,
                   "previous_face_detection_ts":1522130633840,
                   "face_detect_in_processing":true
                  }
    }
*/

function key_face_detect_needed(cameraId){
    var previous_face_detection_ts = getPreviousFaceDetectionTs(cameraId);
    ON_DEBUG && console.log('key_face_detect_needed, lets say, 5fps frame rate, then 1 detect per sec')
    if(!previous_face_detection_ts){
      setPreviousFaceDetectionTs(cameraId, new Date().getTime())
      return true
    } else {
      var current_ts = new Date().getTime()
      if ( current_ts - previous_face_detection_ts > FACE_DETECTION_DURATION ){
        setPreviousFaceDetectionTs(cameraId, current_ts)
        return true
      }
    }
    return false
}

function checkAndNewCameraTrackerInfo(cameraId) {
  if(!cameraId){
      console.log('checkAndNewCameraTrackerInfo no cameraId')
      return false;
  }
  if(!cameras_tracker[cameraId]) {
      cameras_tracker[cameraId] = {'tracker_id_alive_ts': 0,
                                   'current_tracker_id': 0,
                                   'current_person_count': 0,
                                   'current_face_count': 0,
                                   'old_ts': 0,
                                   'previous_face_detection_ts': null,
                                   'face_detect_in_processing': false,
                                   'face_embedding_in_processing': false,
                                   'saved_faces_motion':0}
  }
  return true;
}
function increase_saved_faces_motion(cameraId){
    if(!cameraId || !checkAndNewCameraTrackerInfo(cameraId)) {
        return 0;
    }
    cameras_tracker[cameraId].saved_faces_motion++;
}
function get_saved_faces_motion(cameraId){
    if(!cameraId || !checkAndNewCameraTrackerInfo(cameraId)) {
        return 0;
    }
    return cameras_tracker[cameraId].saved_faces_motion;
}
function setCurrentFaceCount(cameraId, faceNumber) {
  if(!cameraId || !checkAndNewCameraTrackerInfo(cameraId)) {
      return 0;
  }
  cameras_tracker[cameraId].current_face_count = faceNumber;
}
function getCurrentFaceCount(cameraId) {
  if(!cameraId || !checkAndNewCameraTrackerInfo(cameraId)) {
      return 0;
  }
  return cameras_tracker[cameraId].current_face_count;
}
function setCurrentPersonCount(cameraId, faceNumber) {
  if(!cameraId || !checkAndNewCameraTrackerInfo(cameraId)) {
      return 0;
  }
  cameras_tracker[cameraId].current_person_count = faceNumber;
}
function getCurrentPersonCount(cameraId) {
  if(!cameraId || !checkAndNewCameraTrackerInfo(cameraId)) {
      return 0;
  }
  return cameras_tracker[cameraId].current_person_count;
}
function getOldTimeStamp(cameraId) {
  if(!cameraId || !checkAndNewCameraTrackerInfo(cameraId)) {
      return 0;
  }

  return cameras_tracker[cameraId].old_ts
}
function setOldTimeStamp(cameraId, ts) {
  if(!cameraId || !checkAndNewCameraTrackerInfo(cameraId)) {
      return 0;
  }

  cameras_tracker[cameraId].old_ts = ts;
}
function setPreviousFaceDetectionTs(cameraId, previous_face_detection_ts) {
  if(!cameraId || !checkAndNewCameraTrackerInfo(cameraId)) {
      return 0;
  }

  cameras_tracker[cameraId].previous_face_detection_ts = previous_face_detection_ts;
}
function getPreviousFaceDetectionTs(cameraId, previous_face_detection_ts) {
  if(!cameraId || !checkAndNewCameraTrackerInfo(cameraId)) {
      return 0;
  }

  return cameras_tracker[cameraId].previous_face_detection_ts;
}

function getFaceDetectInProcessingStatus(cameraId) {
  if(!cameraId || !checkAndNewCameraTrackerInfo(cameraId)) {
      return 0;
  }

  return cameras_tracker[cameraId].face_detect_in_processing;
}
function setFaceDetectInProcessingStatus(cameraId, face_detect_in_processing) {
  if(!cameraId || !checkAndNewCameraTrackerInfo(cameraId)) {
      return 0;
  }
  cameras_tracker[cameraId].face_detect_in_processing = face_detect_in_processing;
}
function setEmbeddingInProcessingStatus(cameraId, face_embedding_in_processing) {
  if(!cameraId || !checkAndNewCameraTrackerInfo(cameraId)) {
      return 0;
  }
  cameras_tracker[cameraId].face_embedding_in_processing = face_embedding_in_processing;
}
function getEmbeddingInProcessingStatus(cameraId) {
  if(!cameraId || !checkAndNewCameraTrackerInfo(cameraId)) {
      return 0;
  }

  return cameras_tracker[cameraId].face_embedding_in_processing;
}
function getCurrentTrackerId(cameraId) {
  if(!cameraId || (cameras_tracker && !cameras_tracker[cameraId])) {
      return null;
  }

  return cameras_tracker[cameraId].current_tracker_id;
}
function stop_current_tracking(cameraId){
  ON_DEBUG && console.log('to stop_current_tracking: '+cameraId)
  if(!checkAndNewCameraTrackerInfo(cameraId)) {
      return;
  }
  cameras_tracker[cameraId].current_tracker_id = ''
  cameras_tracker[cameraId].tracker_id_alive_ts = null
  cameras_tracker[cameraId].current_person_count = 0
  ON_DEBUG && console.log('TODO: Pass tracker stopped event into system if needed, cameraId: ' + cameraId)
}
function extend_tracker_id_life_time(cameraId){
  ON_DEBUG && console.log('to extend_tracker_id_life_time[ts:'+ cameras_tracker[cameraId].current_tracker_id +']: '+cameraId)
  if(!checkAndNewCameraTrackerInfo(cameraId)) {
      return;
  }
  cameras_tracker[cameraId].tracker_id_alive_ts = new Date().getTime()
  ON_DEBUG && console.log('extend_tracker_id_life_time [ts:'+ cameras_tracker[cameraId].current_tracker_id +'] to: '+cameras_tracker[cameraId].tracker_id_alive_ts)
}
function start_new_tracker_id(cameraId){
  checkAndNewCameraTrackerInfo(cameraId);

  ON_DEBUG && console.log('to start_new_tracker_id '+ cameras_tracker[cameraId].current_tracker_id)

  var ts = new Date().getTime()
  cameras_tracker[cameraId].tracker_id_alive_ts = ts
  cameras_tracker[cameraId].current_tracker_id = ts
  ON_DEBUG && console.log('start_new_tracker_id: '+cameras_tracker[cameraId].current_tracker_id)
}

function is_in_tracking(cameraId){
  if(!checkAndNewCameraTrackerInfo(cameraId)) {
      return false;
  }

  if(!cameras_tracker[cameraId].tracker_id_alive_ts){
    return false
  }
  var current_ts = new Date().getTime()
  var diff = current_ts - cameras_tracker[cameraId].tracker_id_alive_ts
  if( diff < TRACKER_ID_SILIENCE_INTERVAL){
    ON_DEBUG && console.log('still in tracking')
    return true
  } else {
    ON_DEBUG && console.log('Not in tracking, diff is '+diff+' , < ' + TRACKER_ID_SILIENCE_INTERVAL)
  }
  return false
}
function save_image_for_delayed_process(cameraId, file_path, force_saving){
  if(!DEEP_ANALYSIS_MODE && !force_saving){
    ON_DEBUG && console.log('DEEP_ANALYSIS_MODE off, do not save image for delayed process')
    deepeye.delete_image(file_path)
    return
  }
  var current_face_count = getCurrentFaceCount(cameraId)
  var current_tracker_id = getCurrentTrackerId(cameraId)
  if(current_face_count > 0){
    ON_DEBUG && console.log('TODO: save and send to no priority task, faces: '+current_face_count + ' camera: '+cameraId)
    var ts = new Date().getTime()
    waitqueue.waitQueueInsert({'cameraId': cameraId, 'filepath': file_path,
      'ts': ts, 'trackerid':current_tracker_id})
  } else {
    ON_DEBUG && console.log('No faces, no need to do image save')
    deepeye.delete_image(file_path)
  }
}
function js_traverse(o) {
    var type = typeof o
    if (type == "object") {

    } else {
        print(o)
    }
}
function getRecognitionTimes(tracking_info){
  var recognition_times = 0
  if(tracking_info){
    for (var key in tracking_info.results) {
        recognition_times += tracking_info.results[key]
    }
    recognition_times += tracking_info.front_faces
  }
  return recognition_times
}
function getFaceRecognitionTaskList(cameraId,cropped_images,tracking_info,current_tracker_id){
  /*
  cropped_images:
  [ { trackerid: 1542411749715,
    style: 'right_side',
    blury: 334.7526585670141,
    width: 209,
    totalPeople: 1,
    path: '/opt/nvr/detector/images/deepeye_1542411760711_0.png',
    ts: 1542411760730,
    cameraId: 'Lorex_1',
    height: 210 } ]
  tracking_info:
  {
    _id: 1542411749715,
    recognized: true,
    results: { '15392942339300000': 10 },
    front_faces: 1,
    number: 1,
    created_on: 1542411750486
  }
  */
  if(!cropped_images || cropped_images.length === 0){
    return [];
  }
  var time_diff = (new Date() - current_tracker_id)/1000

  ON_DEBUG && console.log('Tracking lasting for %ds, I like this logic game ',time_diff,cropped_images,tracking_info)
  var face_list = []
  cropped_images.sort(function(a,b){
    var area_a = a.height * a.width;
    var area_b = b.height * b.width;
    return area_b - area_a;
  })
  cropped_images.forEach(function(item){
    if(RESTRICT_RECOGNITON_MODE && item.style !== 'front'){
      deepeye.delete_image(item.path)
      ON_DEBUG && console.log('Do not use side face')
      return
    }
    if(item.width < MINIMAL_FACE_RESOLUTION || item.height < MINIMAL_FACE_RESOLUTION){
      ON_DEBUG && console.log('Do not use smaller face than %d',MINIMAL_FACE_RESOLUTION)
      deepeye.delete_image(item.path)
      return
    }
    if(BIGGEST_FACE_ONLY_MODE){
      if(face_list.length >=1){
          ON_DEBUG && console.log('BIGGEST_FACE_ONLY_MODE, skipped one face')
          deepeye.delete_image(item.path)
          return
      }
    }
    face_list.push(item)
  })
  return face_list
}
function do_face_detection(cameraId,file_path,person_count,start_ts,tracking_info,current_tracker_id){
  var ts = new Date().getTime()
  var timeout = setTimeout(function(){
    console.log('timeout of tack do_face_detection, manually recover it')
    setFaceDetectInProcessingStatus(cameraId, false);
  },TASK_IN_DETECTOR_EXPIRE_IN_SECONDS*1000)
  deepeye.process(cameraId, file_path, ts, current_tracker_id,
    function(err,face_detected,cropped_num,cropped_images,whole_file) {
      tracking_info && console.log(tracking_info);
      setFaceDetectInProcessingStatus(cameraId, false);
      clearTimeout(timeout)
      ON_DEBUG && console.log('detect callback')
      if(err) {
          console.log(err)
          //deepeye.delete_image(whole_file)
          return;
      }
      if(typeof person_count === 'undefined'){
        person_count = face_detected
      }
      var current_person_count = getCurrentPersonCount(cameraId)
      console.log('['+cameraId+'] tid: '+current_tracker_id+' person num: '+person_count+' face num: '+face_detected+' cost: '+(new Date() - start_ts));
      setCurrentPersonCount(cameraId, person_count)
      setCurrentFaceCount(cameraId, face_detected)
      if(person_count >= 1){
        extend_tracker_id_life_time(cameraId)
      } else if (face_detected===0){
        stop_current_tracking(cameraId)
        timeline.update(current_tracker_id,'track_stopped',0,null)
      }
      /*else {
        // Keep Tracker ID same if multiple person detected
        console.log('TODO: Multiple Person Logic')
      }*/

       // Person number changed, need handle it
    /*timeline.get_faces_detected(current_tracker_id,function(err,number){
      console.log('Current face number----', number)
      if(number !== 0 && number !== face_detected){
          console.log('number of faces changes.....')
          timeline.update(current_tracker_id,'track_stopped',0,null)
          stop_current_tracking(cameraId)
          start_new_tracker_id(cameraId)
          current_tracker_id = getCurrentTrackerId(cameraId)
          setCurrentPersonCount(cameraId, face_detected)
          }
    */

      var faces_to_be_recognited = getFaceRecognitionTaskList(cameraId,
        cropped_images,tracking_info,current_tracker_id)
      if (faces_to_be_recognited.length >0) {
        // 根据数学的Sampling 原则，我们计算一张图片的Embedding时，只需要确保其他的图片不要计算，而等着一张图片的都计算完
        if(SAMPLING_TO_SAVE_ENERGY_MODE){
          if(getEmbeddingInProcessingStatus(cameraId)){
            console.log('Sampling mode, skip this frame since previous calcuation is in progress, need delete images of faces')

            gifQueue.add({
              person_count:person_count,
              cameraId:cameraId,
              current_tracker_id:current_tracker_id,
              whole_file:whole_file,
              name_sorting:false});
            return
          }
        }

        var embedding_timeout = setTimeout(function(){
          console.log('timeout of tack embedding_clustering, manually recover it')
            setEmbeddingInProcessingStatus(cameraId,false)
        },TASK_IN_DETECTOR_EXPIRE_IN_SECONDS*1000)

        setEmbeddingInProcessingStatus(cameraId,true)
        deepeye.embedding_clustering(faces_to_be_recognited, current_tracker_id, function(err,results){
          setEmbeddingInProcessingStatus(cameraId,false)
          clearTimeout(embedding_timeout)
          timeline.update(current_tracker_id,'in_tracking',person_count,results)

          if(GIF_UPLOADING){
            //save gif info
            var jpg_motion_path = face_motions.save_face_motion_image_path(current_tracker_id, whole_file);
            timeline.push_gif_info(current_tracker_id, jpg_motion_path, results, ts, function(err) {
              if(err){
                console.log(err)
              }
            })
            // after it,the whole_file will be deleted, so need call it after face_motions.save_face_motion_image_path
            gifQueue.add({
              person_count:person_count,
              cameraId:cameraId,
              current_tracker_id:current_tracker_id,
              whole_file:whole_file,
              name_sorting:false});
          } else {
            deepeye.delete_image(whole_file)
          }
        })
      } else {
          if(GIF_UPLOADING){
            gifQueue.add({
              person_count:person_count,
              cameraId:cameraId,
              current_tracker_id:current_tracker_id,
              whole_file:whole_file,
              name_sorting:false});
          } else {
            deepeye.delete_image(whole_file)
          }
      }
    //})
  });
}
gifQueue.process(function(job, done){

  // job.data contains the custom data passed when the job was created
  // job.id contains id of this job.
  ON_DEBUG && console.log('process gif task in bull queue %d',job.id)
  var data = job.data
  face_motions.check_and_generate_face_motion_gif(
    data.person_count,
    data.cameraId,
    data.current_tracker_id,
    data.whole_file,
    data.name_sorting,
    function(err,the_file){
      deepeye.delete_image(data.whole_file)
      done();
  })
});
var delayed_for_face_detection = true;

function need_save_to_delayed_process(tracking_info){
  // 初始阶段，还没有任何检测结果，送入Delayed队列
  if(!tracking_info){
    return true;
  }
  /*
   Tracking Info Format
   {  _id: 1542403488136, // TimeStamp for the first frame of this event
      recognized: false,
      results: { '15392942339300000': 1 },
      front_faces: 0,
      number: 1,
      created_on: 1542403489181
   }
  */
  var recognized_in_results = Object.keys(tracking_info.results).length
  // 如果已经识别出的人数多于当前Tracking的最大人数，不再送入Delayed队列
  if(recognized_in_results >= tracking_info.number){
    console.log('recognized_in_results >= %d, no delayed save',tracking_info.number)
    return false;
  }
  // 镜头前是陌生人，正脸出现次数大于 N，不再入Delayed队列
  if(tracking_info.front_faces >= MAX_UNKNOWN_FRONT_FACE_IN_TRACKING){
    console.log('Unknowd faces >= %d no delayed save',MAX_UNKNOWN_FRONT_FACE_IN_TRACKING)
    return false;
  }
  // 其他情况，入队列
  return true;
}
// Has motion mean in defined duration, motion detected.
// Can define it on WEB GUI
var onframe = function(cameraId, motion_detected, file_path, person_count, start_ts){
  ON_DEBUG && console.log('onframe '+ cameraId +' motion detected frame has motion: '+ motion_detected)
  var previous_diff = new Date().getTime() - getOldTimeStamp(cameraId)
  ON_DEBUG && console.log(previous_diff)
  setOldTimeStamp(cameraId, new Date().getTime())

  var current_tracker_id = false;

  if(motion_detected === true){
    if(is_in_tracking(cameraId)){
      current_tracker_id = getCurrentTrackerId(cameraId)
      // Better to extend it when person_count > 0 only,comment out here.
      //extend_tracker_id_life_time(cameraId)
    } else {
      start_new_tracker_id(cameraId)
    }

    current_tracker_id = getCurrentTrackerId(cameraId)
    // 现在是实时计算阶段，优先快和准要兼顾
    if( delayed_for_face_detection === true &&
      getFaceDetectInProcessingStatus(cameraId) === true ){

      timeline.get_tracking_info(current_tracker_id,
        function(error, tracking_info){
          ON_DEBUG && console.log('to analysis tracking info to decide \
              if save image for delayed processing: ',tracking_info)
          if(need_save_to_delayed_process(tracking_info)){
            save_image_for_delayed_process(cameraId,file_path)
          } else {
            ON_DEBUG && console.log('delete image due to no need save to delayed process')
            deepeye.delete_image(file_path)
          }
      })

      return;
    }
    timeline.get_tracking_info(current_tracker_id,function(error, tracking_info){
      setFaceDetectInProcessingStatus(cameraId, true);
      return do_face_detection(cameraId,file_path,person_count,
        start_ts,tracking_info,current_tracker_id)
    })
  } else if(is_in_tracking(cameraId)){
    // 由于现在没有使用Motion Detection，这里都不会进入
    var current_tracker_id = getCurrentTrackerId(cameraId)
    face_motions.clean_up_face_motion_folder(cameraId,current_tracker_id)
    stop_current_tracking(cameraId)
  }
}
motion.init(onframe)
if(UPLOAD_IMAGE_SERVICE_ENABLED){
  upload_listener.init(onframe)
}
waitqueue.init()

const express = require('express');
const app = express();
const router = express.Router();
const port = 3000;

app.get('/', (request, response) => response.send('SharpAI, empower Edge AI'));

app.use('/api', router);
app.use(express.json());

router.get('/post', (request, response) => {
    file_url = request.originalUrl
    filename = file_url.substring(file_url.indexOf('=')+1)
    console.log(filename)
    setTimeout(function(){
       var undefined_obj
       var start = new Date()
       onframe("device", true, filename, undefined_obj, start)
    }, 0)
    response.json({message: 'OK'});
});

app.post('/post2',function(request, response) {
  console.log(request.body);
  response.json({message: 'OK'});
})
app.listen(port,'0.0.0.0' ,() => console.log('Listening on port ',port));
