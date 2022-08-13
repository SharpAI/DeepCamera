var deepeye=require('./deepeye')
var timeline=require('./timeline')

var wait_detect_queue = [];
var ON_DEBUG = false
var processWaitQueueInterval = null;
function GetEnvironmentVarInt(varname, defaultvalue)
{
    var result = process.env[varname];
    if(result!=undefined)
        return parseInt(result,10);
    else
        return defaultvalue;
}

var MINIMAL_FACE_RESOLUTION = GetEnvironmentVarInt('MINIMAL_FACE_RESOLUTION', 200)
var DEEP_ANALYSIS_MODE = GetEnvironmentVarInt('DEEP_ANALYSIS_MODE',1)

function need_do_face_recognition(tracking_info){
  // No need to do face recognition at the early stage 
  if(!tracking_info){
    return true;
  }
  // Do face recognition if deep analysis mode enabled
  if(DEEP_ANALYSIS_MODE){
    ON_DEBUG && console.log('---------deep analysis mode enabled--------')
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
  // No need to do face recognition if recognized faces are greater than maximal tracking number. 
  if(recognized_in_results >= tracking_info.number){
    console.log('recognized_in_results >= %d, skip delayed process',tracking_info.number)
    return false;
  }
  // No need to do face recognition if number of stranger's front face greater than N
  if(tracking_info.front_faces >= tracking_info.number){
    console.log('Unknowd faces >= %d skip delayed process',tracking_info.number)
    return false;
  }
  // else do face recognition 
  return true;
}

function getLargeFrontFacesList(cropped_images){
  if(DEEP_ANALYSIS_MODE){
    console.log('---cropped images length-----',cropped_images.length)
    return cropped_images
  }

  var face_list=[]
  cropped_images.forEach(function(item){
    if(item.style !== 'front'){
      deepeye.delete_image(item.path)
      console.log('Do not use side face')
      return
    }
    if(item.width < MINIMAL_FACE_RESOLUTION || item.height < MINIMAL_FACE_RESOLUTION){
      console.log('Do not use smaller face than %d',MINIMAL_FACE_RESOLUTION)
      deepeye.delete_image(item.path)
      return
    }
    face_list.push(item)
  })
  return face_list
}
function processWaitQueue() {
    if(wait_detect_queue.length <1) {
        ON_DEBUG && console.log("empty wait queue")
        return;
    }

    deepeye.getQueueLenth(function(err, started_task_num) {
        if(err) {
            console.log(err)
            return;
        }
        console.log('task in delayed processing is '+wait_detect_queue.length+' celery queue is: '+started_task_num)
        if(started_task_num < 1) {
            var task = wait_detect_queue.shift()
            if(!task){
              ON_DEBUG && console.log("no task in queue")
              return;
            }
            timeline.get_tracking_info(task.trackerid,
              function(error, tracking_info){
                console.log('deleyed process, tracking_info:',tracking_info)
                if(!need_do_face_recognition(tracking_info)){
                  console.log('tracking %d no need furthur recognition, lets clean up next one',task.trackerid)
                  deepeye.delete_image(task.filepath)
                  setTimeout(processWaitQueue,0)
                  return
                }
                deepeye.processSavedTask(task.cameraId, task.filepath, task.ts, task.trackerid,
                  function(err,cropped_num,cropped_images) {
                    if(err) {
                      console.log('need check deepeye.processSavedTask error')
                      console.log(err)
                      return
                    }

                   var trackerId = task.ts;
                   ON_DEBUG && console.log(">>>>> " + JSON.stringify(cropped_images))
                   var front_large_faces = getLargeFrontFacesList(cropped_images)
                   if (front_large_faces.length>0) {
                       console.log('do embedding after waitqueue---------')
                       deepeye.embedding(front_large_faces, trackerId,function(err,results){
                         console.log('Got result on delayed task: '+results)
                         timeline.update(trackerId,'delayed',cropped_num,results,function(){
                           timeline.get_face_ids(trackerId,function(err,results){
                             console.log(results)
                           })
                         })
                       });
                   }
                })
                ON_DEBUG && console.log(">>>>get one task: " + JSON.stringify(task))
            })
        }
    })
}

module.exports = {
  init: function _queueInit() {
      wait_detect_queue = []
      processWaitQueueInterval = setInterval(processWaitQueue, 500);
      console.log("wait detect queue init ")
  },
  waitQueueInsert: function _waitQueueInsert(task) {
      wait_detect_queue.push(task)
      ON_DEBUG && console.log(">>>>waitQueueInsert " + JSON.stringify(task) + " " + wait_detect_queue.length)
  }
}
