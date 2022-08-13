
var fs = require('fs')
var url = require('url')
var path = require('path')

var readdir = require('readdir-absolute')
var express = require('express')
var bodyParser = require('body-parser')
var Queue = require('better-queue')
var download = require('download-file')
var ffmpeg = require('fluent-ffmpeg')
var mkdirp = require('mkdirp')
var async = require('async')
var socket_io = require('socket.io-client')('http://12.206.217.173:3000', {
    reconnection: true,
    reconnectionDelay: 1000,
    reconnectionDelayMax : 5000,
    reconnectionAttempts: 99999
})

var deepeye = require('./deepeye')
var face_motions=require('./face_motions')
var timeline=require('./timeline')

var VIDEO_DIR = '/opt/nvr/videos/';
var FRAME_DIR = '/opt/nvr/videos/frames/'

var CAMERA_ID = 'Alro'
var VIDEO_FRAME_PER_SEC = 3
var TRACKER_ID_GAP_DURATION = 10
var FRAMES_TO_SET_NEW_TRACKER_ID = TRACKER_ID_GAP_DURATION * VIDEO_FRAME_PER_SEC

var last_tracker_id_check_frame = 0
var tracker_id
var file_timestamp = 0

var frame_info = { frame_num : 0 }

function setup_tracker_id(){
  tracker_id = new Date().getTime()
  file_timestamp = tracker_id
  last_tracker_id_check_frame = 0
}
function get_tracker_id(){
  return tracker_id
}
function stop_current_tracking(){
  console.log('stop current tracking '+tracker_id)
}
function update_tracker_id(face_detected,current_frame,cb){
  if(face_detected > 0){
    last_tracker_id_check_frame = current_frame
    return cb && cb(false)
  } else if(current_frame - last_tracker_id_check_frame > FRAMES_TO_SET_NEW_TRACKER_ID){
    var current_tracker_id = get_tracker_id()
    timeline.update(current_tracker_id,'track_stopped',0,null)
    stop_current_tracking()
    setup_tracker_id()
    last_tracker_id_check_frame = current_frame
    return cb && cb(true)
  }
}
function get_ts_by_frame_num(frame_num){
  return file_timestamp + (frame_num * 1000 / VIDEO_FRAME_PER_SEC)
}
function do_face_detection(file_path,frame_num,cb){
  var cameraId = CAMERA_ID
  var ts = get_ts_by_frame_num(frame_num)
  deepeye.processSavedTask(cameraId, file_path, ts,
    function(err,cropped_num,cropped_images,face_detected) {
      var current_tracker_id = get_tracker_id()
      update_tracker_id(face_detected,frame_num,function(tracking_stopped){
        if(tracking_stopped){
          face_motions.check_and_generate_face_motion_gif(0,
            cameraId,current_tracker_id,file_path,true)
        } else if(face_detected > 0){
          face_motions.check_and_generate_face_motion_gif(face_detected,
            cameraId,current_tracker_id,file_path,true)
        }
      })
      if (cropped_num>0) {
        deepeye.embedding(cropped_images, current_tracker_id,function(err,results){
          console.log(results)
          if(!err && results){
            timeline.update(current_tracker_id,'in_tracking',cropped_num,results)
            return cb && cb(null,results)
          } else {
            return cb && cb(null,null)
          }
        })
      } else {
        return cb && cb(null,null)
      }
  });
}

function process_frames(type,dir,cb){
  readdir(dir,function(err,list){
    var files = list.filter(function(element) {
      var extName = path.extname(element);
      return extName === '.'+type;
    }).sort(function(a, b) {
      var a_num = parseInt(/frame-(.*?).jpg/.exec(a.toString())[1])
      var b_num = parseInt(/frame-(.*?).jpg/.exec(b.toString())[1])
      return a_num - b_num
    });

    if (files.length > 0){
      setup_tracker_id()
      frame_info.frame_num = 0
      async.each(files, function(file,callback){
        do_face_detection(file,frame_info.frame_num++,function(err,result){
          //setTimeout(function(){
            callback(null,result)
          //},100)
        })
      }, function(err,results){
      // if any of the saves produced an error, err would equal that error
        var current_tracker_id = get_tracker_id()
        var cameraId = CAMERA_ID
        face_motions.check_and_generate_face_motion_gif(0,
            cameraId,current_tracker_id,'',true)
        return cb && cb(null,results)
      });
    } else if(cb){
      cb('No File in folder: '+dir,null)
    }
  });
}
var q = new Queue(function (task_info, cb) {
  // Some processing here ...
  console.log(task_info)
  if(task_info && task_info.url){
    console.log('to download: '+ task_info.url)

    var parsed = url.parse(task_info.url)
    var filename = path.basename(parsed.pathname)
    var basename = filename.toString().replace(/\.[^/.]+$/, "")
    var options = {
        directory: VIDEO_DIR,
        filename: filename
    }

    var frame_dir = FRAME_DIR + basename + '/'

    console.log('start download');
    mkdirp(frame_dir, function (err) {
      try {
        var cmd = ffmpeg(task_info.url)
          .on('start',function(cmd){
            console.log(cmd)
          })
          .outputOptions([
            '-vf', 'fps=3',
            '-qscale:v', 2/*,
            '-vf', "scale=-1:480"*/
          ])
          .on('end',function(result){
            console.log('end')
            console.log(result)
            process_frames('jpg',frame_dir,function(){
              cb(null, 'ok')
            })
          })
          .on('error',function(err){
            console.log('err end')
            console.log(err)
            cb(err, null)
          })
          .output(frame_dir+'frame-%d.jpg')
          .run()
      } catch (e) {
        console.log(e.code);
        console.log(e.msg);
        cb('Error in ffmpeg', e)
      }
    });

    /*download(task_info.url, options, function(err){
        if (err) {
          cb('download error', err)
          return
        }
        var file_path = path.resolve(VIDEO_DIR+filename)

        console.log("downloaded: "+file_path)

    })*/
  } else {
    cb('Error', 'query error')
  }
})

q.on('task_finish', function (taskId, result, stats) {
  // taskId = 1, result: 3, stats = { : <time taken> }
  // taskId = 2, result: 5, stats = { elapsed: <time taken> }
  console.log('task [' + taskId +'] finish: '+result + ' time taken: ' + stats.elapsed)
})
q.on('task_failed', function (taskId, err, stats) {
  console.log('task [' + taskId +'] failed: '+err + stats)
})
q.on('empty', function (){
  console.log('queue empty')
})
q.on('drain', function (){
  console.log('queue drain')
})

//q.push(1)
//q.push({ x: 1 })


var app = express();
var port = process.env.PORT || 8080;

// routes will go here

//support parsing of application/json type post data
app.use(bodyParser.json());
//support parsing of application/x-www-form-urlencoded post data
app.use(bodyParser.urlencoded({ extended: true }));

app.post('/api/insert', function(req, res) {

  console.log(req.body)
  var download_url = req.body.download_url
  q.push({url:download_url})
  console.log('download url: '+download_url)
  res.send('ok');
});

socket_io.on('connect', function(){
    console.log("connect")
});
socket_io.on('message', function (message) {
  if(message){
    console.log("message:", message)
    q.push({url:message})
  }
});

// start the server
app.listen(port);
console.log('Server started! At http://localhost:' + port);

// do test
// require('./test_post')
