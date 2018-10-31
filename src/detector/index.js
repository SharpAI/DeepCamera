
process.on('uncaughtException', function (err) {
    console.error('uncaughtException',err)
});

var motion=require('./motion_clean')
//var motion=require('./od')
var deepeye=require('./deepeye')
var waitqueue=require('./waitqueue')
var timeline=require('./timeline')
var face_motions=require('./face_motions')

rt_msg = require('./realtime_message')

var ON_DEBUG = false
var FACE_DETECTION_DURATION = 100 // MS, fixed value implement first
var TRACKER_ID_SILIENCE_INTERVAL = 4000 // MS, fixed value implement first

var cameras_tracker = {}

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
  console.log('TODO: Pass tracker stopped event into system if needed, cameraId: ' + cameraId)
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
  console.log('start_new_tracker_id: '+cameras_tracker[cameraId].current_tracker_id)
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
function save_image_for_delayed_process(cameraId, file_path){
  var current_face_count = getCurrentFaceCount(cameraId);
  var current_tracker_id = getCurrentTrackerId(cameraId)
  if(current_face_count > 0){
    ON_DEBUG && console.log('TODO: save and send to no priority task, faces: '+current_person_count + ' camera: '+cameraId)
    var ts = new Date().getTime()
    waitqueue.waitQueueInsert({'cameraId': cameraId, 'filepath': file_path,
      'ts': ts, 'trackerid':current_tracker_id})
  } else {
    ON_DEBUG && console.log('No faces, no need to do image save')
    deepeye.delete_image(file_path)
  }
}
function do_face_detection(cameraId,file_path,person_count,start_ts){
  var ts = new Date().getTime()
  var current_tracker_id = getCurrentTrackerId(cameraId)
  deepeye.process(cameraId, file_path, ts, current_tracker_id,
    function(err,face_detected,cropped_num,cropped_images,whole_file) {
      setFaceDetectInProcessingStatus(cameraId, false);
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
      console.log('tracker id: '+current_tracker_id+'person count: '+person_count+' face count: '+face_detected+' time cost: '+(new Date() - start_ts));
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

      if (cropped_num>0) {
        var trackerId = getCurrentTrackerId(cameraId)
        deepeye.embedding(cropped_images, current_tracker_id, function(err,results){
          timeline.update(current_tracker_id,'in_tracking',person_count,results)

          //save gif info
          var jpg_motion_path = face_motions.save_face_motion_image_path(current_tracker_id, whole_file);
          timeline.push_gif_info(current_tracker_id, jpg_motion_path, results, ts, function(err) {
            if(err)
              console.log(err)

          })

          face_motions.check_and_generate_face_motion_gif(person_count,
            cameraId,current_tracker_id,whole_file,false,
            function(err,the_file){
              deepeye.delete_image(whole_file)
          })
        })
      }
      else {
        face_motions.check_and_generate_face_motion_gif(person_count,
          cameraId,current_tracker_id,whole_file,false,
          function(err,the_file){
            deepeye.delete_image(whole_file)
        })
      }


    //})
  });
}

var delayed_for_face_detection = true;

// Has motion mean in defined duration, motion detected.
// Can define it on WEB GUI
var onframe = function(cameraId, motion_detected, file_path, person_count, start_ts){
  ON_DEBUG && console.log('onframe '+ cameraId +' motion detected frame has motion: '+ motion_detected)
  var previous_diff = new Date().getTime() - getOldTimeStamp(cameraId)
  ON_DEBUG && console.log(previous_diff)
  setOldTimeStamp(cameraId, new Date().getTime())

  if( delayed_for_face_detection === true && getFaceDetectInProcessingStatus(cameraId) === true ){
    save_image_for_delayed_process(cameraId,file_path)

    return;
  }
  if(motion_detected === true){
    if(is_in_tracking(cameraId)){
      extend_tracker_id_life_time(cameraId)
      if(delayed_for_face_detection === true){
        setFaceDetectInProcessingStatus(cameraId, true);
        return do_face_detection(cameraId,file_path,person_count,start_ts)
      } else {
          setFaceDetectInProcessingStatus(cameraId, true);
          return do_face_detection(cameraId,file_path,person_count,start_ts)
      }
    } else {
      start_new_tracker_id(cameraId)
      setFaceDetectInProcessingStatus(cameraId, true);
      return do_face_detection(cameraId,file_path,person_count,start_ts)
    }
  } else if(is_in_tracking(cameraId)){
    var current_tracker_id = getCurrentTrackerId(cameraId)
    face_motions.clean_up_face_motion_folder(cameraId,current_tracker_id)
    stop_current_tracking(cameraId)
  }
}
motion.init(onframe)
waitqueue.init()
