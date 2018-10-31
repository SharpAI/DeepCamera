var deepeye=require('./deepeye')
var timeline=require('./timeline')

var wait_detect_queue = [];
var ON_DEBUG = false
var processWaitQueueInterval = null;

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
            deepeye.processSavedTask(task.cameraId, task.filepath, task.ts, task.trackerid,
              function(err,cropped_num,cropped_images) {
                if(err) {
                  console.log('need check deepeye.processSavedTask error')
                  console.log(err)
                  return
                }

               var trackerId = task.ts;
               ON_DEBUG && console.log(">>>>> " + JSON.stringify(cropped_images))
               if (cropped_num>0) {
                   deepeye.embedding(cropped_images, trackerId,function(err,results){
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
