var Canvas = require('canvas');
var fs = require('fs');
var http = require('http');
var qs=require('querystring');
var path = require('path');
var request = require('request');
var celery = require('node-celery');

var async = require('async')
var face_motion = require('./face_motions')
var maintainer = require('./maintainer')
var mqtt_2_group = require('./mqttgif')
var timeline = require('./timeline')
var device_SN = null

var host_ip = 'flower'
//var host_ip = '192.168.3.3'
var detect_task_url = 'http://'+host_ip+':5555/api/task/apply/upload_api-v2.detect'
var detect_task_queues_length = 'http://'+host_ip+':5555/api/tasks?limit=100&state=STARTED&workername=celery%40detect'
var embedding_task_queues_length = 'http://'+host_ip+':5555/api/tasks?limit=100&state=STARTED&workername=celery%40embedding'
var embedding_task_url = 'http://'+host_ip+':5555/api/task/apply/upload_api-v2.extract'
var IMAGE_DIR = process.env.NODE_ENV || '/opt/nvr/detector/images';

var DEVICE_UUID_FILE = '/dev/ro_serialno'
var DEVICE_GROUP_ID = '/data/usr/com.deep.workai/cache/groupid.txt'
//client = null

function connect_node_celery_to_amqp(){
  client = celery.createClient({
    CELERY_BROKER_URL: 'redis://redis/0',
    CELERY_RESULT_BACKEND: 'redis://redis/0',
    TASK_RESULT_EXPIRES: 60,
    CELERY_ROUTES: {
      'upload_api-v2.detect': {
        queue: 'detect'
      },
      'upload_api-v2.extract': {
        queue: 'embedding'
      },
      'upload_api-v2.fullimage': {
        queue: 'nopriority'
      },
      'od.detect': {
        queue: 'od'
      }
    }
  });

  client.on('connect', function() {
    connected_to_celery_broker = true
    console.log('The connection to celery broker is connected')
  });
  client.on('error', function(err) {
      console.log(err)
      connected_to_celery_broker = false
      console.log('The connection to celery broker has error');
      setTimeout(function(){
        console.log('retry to connect to celery broker')
        connect_node_celery_to_amqp()
      },5000)
  });
}
if(typeof client === 'undefined'){
  connected_to_celery_broker = false
  connect_node_celery_to_amqp()
}

var ON_DEBUG = false
module.exports = {
  delete_image:delete_image,
  buffer2file: buffer2file,
  process : function post2workaipython_test(cameraId, file_path,ts,trackerid, cb) {
      detect_task(file_path, trackerid, ts, cameraId, function (err, numFaces, cropped){
          if(err || !cropped) {
            //delete_image(filepath)
            console.log(err)
            console.log(cropped)
            if(err){
                maintainer.onError('face detection',err)
            }
            return cb && cb("add detect_task failed!!", 0, 0, [],null,null)
          }
          return cb && cb(null, numFaces, cropped.length, cropped, file_path)
      })
  },
  object_detection : function (cameraId, file_path, cb) {
      var ts = new Date().getTime()
      object_detection_task(file_path, '', ts, cameraId, function (err, person_count){
          if(err) {
            //delete_image(filepath)
            console.log(err)
            //if(err){
            //    maintainer.onError('face detection',err)
            //}
            return cb && cb("add object_detection_task failed!!", 0, file_path)
          }
          return cb && cb(null, person_count, file_path)
      })
  },
  processSavedTask: function _processSavedTask(cameraId, filepath, ts,trackerid, cb) {
      detect_task(filepath, trackerid, ts, cameraId, function (err, face_detected, cropped){

          delete_image(filepath)
          if(err || !cropped) {
            console.log(err)
            console.log(cropped)
            if(err){
                maintainer.onError('face detection',err)
            }
            return cb && cb("add detect_task failed!!", 0, [], 0)
          }
          return cb && cb(null, cropped.length, cropped, face_detected)
      })
  },
  saveCanvas2png: function _saveCanvas2png(cameraId, image, cb) {
      canvas2png(cameraId, image, IMAGE_DIR, function(err, filepath){
          return cb && cb(err, filepath)
      })
  },
  getQueueLenth: function(cb){
    _getEmbeddingQueueLenth(function(error,task_number){
      if(task_number>0){
        return cb && cb(null,task_number+1)
      } else {
        return cb && cb(null,task_number)
        /*_getDetectQueueLenth(function(err,detect_task_number){
          return cb && cb(null,detect_task_number)
        })*/
      }
    })
  },
  embedding : function embedding_caculation(cropped_images, trackerId, cb) {
    var index = 0;

    async.mapSeries(cropped_images, function(img,callback){
      if(trackerId){
        img.trackerid = trackerId
      }

      if(cropped_images.length>1) {
        if(img && img.ts) {
          img.trackerid = '' + img.trackerid + img.ts
        }
        else {
          img.trackerid = '' + img.trackerid + index;
        }
      }
      index ++;

      ON_DEBUG && console.log(img)
      embedding_task(img, function(err,result) {
        //console.log(result)
        callback(null,result)
      })
    }, function(err, results){
      if(err){
        console.log('Error in Embedding Task')
        console.log(err)
        return cb && cb(err,null)
      } else {
        return cb && cb(null,results)
      }
    });

  }
}
function _getDetectQueueLenth(cb) {
  request({
      url: detect_task_queues_length,
      method: "GET",
      json: true
  }, function (error, response, body){
      if(error) {
          console.log(error)
          return cb && cb(error, 100)
      } else if(body){
          ON_DEBUG && console.log(body)
          return cb && cb(null, Object.keys(body).length)
      } else {
          console.log('>>>> ERROR When flower dont response queue request')
          console.log(body)
          return cb && cb(null, 100)
      }
  })
}
function _getEmbeddingQueueLenth(cb) {
  request({
      url: embedding_task_queues_length,
      method: "GET",
      json: true
  }, function (error, response, body){
      if(error) {
          console.log(error)
          return cb && cb(error, 100)
      } else if(body){
          ON_DEBUG && console.log(body)
          return cb && cb(null, Object.keys(body).length)
      } else {
          console.log('>>>> ERROR When flower dont response queue request')
          console.log(body)
          return cb && cb(null, 100)
      }
  })
}
function object_detection_task(file_path, trackerid, ts, cameraId, cb) {
  if(connected_to_celery_broker){
    client.call('od.detect',
      [file_path,trackerid,ts,cameraId],
      function(result){
        ON_DEBUG && console.log(result)
        if(result && result.status === 'SUCCESS'){
          /*if(result.result){
            var json = JSON.parse(result.result)
            ON_DEBUG && console.log('print result result-----',json)
            if(json.url){
                get_device_uuid(function(uuid){
                    get_device_group_id(function(group_id){
                        ON_DEBUG && console.log('post box img to group....',json.url)
                        mqtt_2_group.post_gif_2_group('box',json.url,uuid,group_id)
                    })
                })
            }
            if((json.totalmtcnn > 0) || (json.detected && json.totalPeople > 0)) {
                return cb && cb(null, json.totalmtcnn, json.cropped)
            }
          }*/
          if(result.result){
              var json = JSON.parse(result.result)
              if(json.detected === true){
                var person_count = 0
                json.results.forEach(function(item){
                  ON_DEBUG && console.log(item)
                  if(item['name'] === 'person'){
                    ON_DEBUG && console.log('has person')
                    person_count++
                  }
                })
                ON_DEBUG && console.log('person count: '+person_count)
                return cb && cb(null, person_count)
              }
          }
          return cb && cb(null, 0)
        } else {
          return cb && cb('error', 0)
        }
    });
  } else {
    console.log('Abnormal situation, not connected to celery broker. Please check this')
    return cb && cb('error', 0, null)
  }
}
function detect_task(file_path, trackerid, ts, cameraId, cb) {
  /*
    motion_1        |   { status: 'SUCCESS',
    motion_1        |   traceback: null,
    motion_1        |   result: '{"totalPeople": 0, "detected": false, "totalmtcnn": 0, "ts": 1526068621089, "cropped": []}',
    motion_1        |   task_id: '92926fbb-cae4-48a0-bd84-4d9c1bf5d1fb',
    motion_1        |   children: [] }
  */
  if(connected_to_celery_broker){
    client.call('upload_api-v2.detect',
      [file_path,trackerid,ts,cameraId],
      function(result){
        ON_DEBUG && console.log(result)
        if(result && result.status === 'SUCCESS'){
          if(result.result){
            var json = JSON.parse(result.result)
            if((json.totalmtcnn > 0) || (json.detected && json.totalPeople > 0)) {
                return cb && cb(null, json.totalmtcnn, json.cropped)
            }
          }
          return cb && cb(null, 0, [])
        } else {
          return cb && cb('error', 0, null)
        }
    });
  } else {
    console.log('Abnormal situation, not connected to celery broker. Please check this')
    return cb && cb('error', 0, null)
  }
}

function embedding_task(cropped_file_path, cb) {
  if(connected_to_celery_broker){
    client.call('upload_api-v2.extract',
      [cropped_file_path],
      function(result){
        ON_DEBUG && console.log(result)
        if(result && result.status === 'SUCCESS'){
          if(result.result){
            var json = JSON.parse(result.result)
            return cb && cb(null, json)
          }
        }
        return cb && cb('error', null)
    });
  } else {
    console.log('Abnormal situation, not connected to celery broker. Please check this')
    return cb && cb('error', null)
  }
}

function detect_task_flower(file_path, trackerid, ts, cameraId, cb) {
    var json_request_content = {'args': [file_path, trackerid, ts, cameraId]};
    console.log('request task url: ', detect_task_url)
    request({
        url: detect_task_url,
        method: "POST",
        json: true,
        body: json_request_content
    }, function (error, response, body){
        if(error) {
            console.log(error)
            return cb && cb(error, 0, null)
        } else {
            console.log('task request body: ',body)
            if(body && body.state=="SUCCESS" && body.result) {
                var json = JSON.parse(body.result)
                console.log('return detection url: '+ body.url)
                if((json.totalmtcnn > 0) || (json.detected && json.totalPeople > 0)) {
                    return cb && cb(null, json.totalmtcnn, json.cropped)
                }
            }
            return cb && cb(null, 0, [])
        }
    });
}
function embedding_task_flower(cropped_file_path, cb) {
    var json_request_content = {'args': [cropped_file_path]};
    request({
        url: embedding_task_url,
        method: "POST",
        json: true,
        body: json_request_content
    }, function (error, response, body){
        if(error) {
            console.log(error)
            return cb && cb(error, null)
        } else {
            ON_DEBUG && console.log(body)
            if(body && body.state=="SUCCESS" && body.result) {
                var json = JSON.parse(body.result)
                return cb && cb(null, json)
            } else {
              return cb && cb('error', null)
            }
        }
    });
}

function get_device_SN(cb) {
    if(device_SN)
        return cb && cb(null, device_SN)

    fs.readFile('/dev/ro_serialno', 'utf8', function(err, data){
        if(err)
            return cb && cb(err, null)

        var arr = data.split('\n')
        if(arr && arr[0] && arr[0] != '') {
            device_SN = arr[0]
            return cb && cb(null, device_SN)
        }
        else {
            return cb && cb(null, null)
        }
    });
}

function get_device_uuid(cb){
  fs.readFile(DEVICE_UUID_FILE, function (err,data) {
    if (err) {
      return cb && cb('no_uuid')
    }
    return cb && cb(data.toString().replace(/(\r\n\t|\n|\r\t)/gm,""))
  });
}

function get_device_group_id(cb){
    fs.readFile(DEVICE_GROUP_ID, function (err,data) {
      if (err) {
        return cb && cb('no_group_id')
      }
      return cb && cb(data)
    });
}
function buffer2file(cameraId, buffer, cb) {
    //get_device_SN(function(snerr, SN){
    //    if(snerr || !SN) {
    //        return cb && cb("get_device_SN failed !!")
    //    }
    //})
    var filename = IMAGE_DIR + '/deepeye_' + cameraId + "_" + (new Date().getTime()) + '.jpg'
    var out = fs.createWriteStream(filename)
    out.on('finish',function(){
        ON_DEBUG && console.log('flushded to disk in pipe end in out.finish()')
        ON_DEBUG && console.log("canvas2jpg end");
        ON_DEBUG && console.log("save as " + filename)
        //out.close()
        return cb && cb(null, filename);
    });

    out.on('error', function (err) {
        console.log("canvas2jpg error: " + err);
        return cb && cb('error', null);
    })
    out.write(buffer);
    out.end();
    //return cb && cb(null, filename);
}
function canvas2png(cameraId, image, dir, cb) {
    //get_device_SN(function(snerr, SN){
    //    if(snerr || !SN) {
    //        return cb && cb("get_device_SN failed !!")
    //    }
    //})
    var canvas1 = new Canvas(image.width, image.height);
    var ctx = canvas1.getContext('2d')
    ctx.drawImage(image, 0, 0, image.width, image.height)

    var filename = dir + '/deepeye_' + cameraId + "_" + (new Date().getTime()) + '.jpg'
    var out = fs.createWriteStream(filename)
    var stream = canvas1.jpegStream({
        bufsize: 4096,
        quality: 100
    })
    out.on('finish',function(){
        ON_DEBUG && console.log('flushded to disk in pipe end in out.finish()')
        ON_DEBUG && console.log("canvas2jpg end");
        ON_DEBUG && console.log("save as " + filename)
        canvas1 = null
        out.close()
        return cb && cb(null, filename);
    });

    out.on('error', function (err) {
        console.log("canvas2jpg error: " + err);
        return cb && cb('error', null);
    })
    stream.pipe(out);
}

function delete_image(filepath) {
    fs.exists(filepath, function(exists) {
        if(!exists) {
            return
        }

        fs.unlink(filepath,function(err){
            if(err) {
                console.log(err)
            }
            else {
                ON_DEBUG && console.log("remove file: " + filepath)
            }
        });
    })
}
