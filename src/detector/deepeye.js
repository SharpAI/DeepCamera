var fs = require('fs');
var http = require('http');
var qs=require('querystring');
var path = require('path');
var request = require('request');
var celery = require('node-celery');
var requestretry = require('requestretry')

var async = require('async')
var face_motion = require('./face_motions')
//var maintainer = require('./maintainer')
var mqtt_2_group = require('./mqttgif')
var timeline = require('./timeline')
var upload = require('./upload')
var device_SN = null

var host_ip = process.env.FLOWER_ADDRESS || 'flower'
var host_port = process.env.FLOWER_PORT || 5555
//var host_ip = '192.168.3.3'
var detect_task_url = 'http://'+host_ip+':'+host_port+'/api/task/apply/upload_api-v2.detect'
var detect_task_queues_length = 'http://'+host_ip+':'+host_port+'/api/tasks?limit=100&state=STARTED&workername=celery%40detect'
var embedding_task_queues_length = 'http://'+host_ip+':'+host_port+'/api/tasks?limit=100&state=STARTED&workername=celery%40embedding'
var embedding_task_url = 'http://'+host_ip+':'+host_port+'/api/task/apply/upload_api-v2.extract'
var IMAGE_DIR = process.env.NODE_ENV || '/opt/nvr/detector/images';

var DEVICE_UUID_FILEPATH = process.env.DEVICE_UUID_FILEPATH || '/dev/ro_serialno'
var DEVICE_GROUP_ID_FILEPATH = process.env.DEVICE_GROUP_ID_FILEPATH || '/data/usr/com.deep.workai/cache/groupid.txt'
//client = null
var REDIS_HOST = process.env.REDIS_HOST || "redis"
var REDIS_PORT = process.env.REDIS_PORT || 6379

var CLUSTER_REDIS_ADDRESS = process.env.CLUSTER_REDIS_ADDRESS || "redis"
var CLUSTER_REDIS_PORT = process.env.CLUSTER_REDIS_PORT || 6379

function GetEnvironmentVarInt(varname, defaultvalue)
{
    var result = process.env[varname];
    if(result!=undefined)
        return parseInt(result,10);
    else
        return defaultvalue;
}
// ONE_KNOWN_PERSON_BYPASS_QUEUE_MODE 一张图里，出现一个人脸，不再计算后续
var ONE_KNOWN_PERSON_BYPASS_QUEUE_MODE = GetEnvironmentVarInt('ONE_KNOWN_PERSON_BYPASS_QUEUE_MODE', 1)
// TASK_EXECUTOR_EXPIRE_IN_SECONDS Celery重启的时候，已经发出的任务不会超时，将导致永远不再执行
var TASK_EXECUTOR_EXPIRE_IN_SECONDS = GetEnvironmentVarInt('TASK_EXECUTOR_EXPIRE_IN_SECONDS', 30)
// 任务并发执行数量
var CLUSTER_CONCURRENCY = GetEnvironmentVarInt('CLUSTER_CONCURRENCY', 1)

function connect_node_celery_to_cluster(){
  cluster_client = celery.createClient({
    CELERY_BROKER_URL: 'redis://'+CLUSTER_REDIS_ADDRESS+':'+CLUSTER_REDIS_PORT+'/0',
    CELERY_RESULT_BACKEND: 'redis://'+CLUSTER_REDIS_ADDRESS+':'+CLUSTER_REDIS_PORT+'/0',
    TASK_RESULT_EXPIRES: 60,
    CELERY_ROUTES: {
      'upload_api-v2.extract_v2': {
        queue: 'embedding'
      }
    }
  });

  cluster_client.on('connect', function() {
    connected_to_celery_cluster = true
    console.log('The connection to celery cluster is connected')
  });
  cluster_client.on('error', function(err) {
      console.log(err)
      connected_to_celery_cluster = false
      console.log('The connection to celery cluster has error');
      setTimeout(function(){
        console.log('retry to connect to celery cluster')
        connect_node_celery_to_cluster()
      },5000)
  });
}
if(typeof cluster_client === 'undefined'){
  connected_to_celery_cluster = false
  connect_node_celery_to_cluster()
}

function celery_task_expires_option(){
  return {
  		expires: new Date(Date.now() + TASK_EXECUTOR_EXPIRE_IN_SECONDS * 1000) // expires in TASK_EXECUTOR_EXPIRE_IN_SECONDS
  }
}

function connect_node_celery_to_amqp(){
  client = celery.createClient({
    CELERY_BROKER_URL: 'redis://'+REDIS_HOST+':'+REDIS_PORT+'/0',
    CELERY_RESULT_BACKEND: 'redis://'+REDIS_HOST+':'+REDIS_PORT+'/0',
    TASK_RESULT_EXPIRES: 60,
    CELERY_ROUTES: {
      'upload_api-v2.detect': {
        queue: 'detect'
      },
      'classify.classify': {
        queue: 'classify'
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
                //maintainer.onError('face detection',err)
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
                //maintainer.onError('face detection',err)
            }
            return cb && cb("add detect_task failed!!", 0, [], 0)
          }
          return cb && cb(null, cropped.length, cropped, face_detected)
      })
  },
  getQueueLenth: function _getQueueLenth(cb) {
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
      });
  },
  embedding : function embedding_caculation(cropped_images, trackerId, cb) {
    var index = 0;
    var recognized_results=[];

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
      if(ONE_KNOWN_PERSON_BYPASS_QUEUE_MODE && recognized_results.length>0){
        console.log('skipped in bypass mode, recognized_results ',recognized_results)
        callback(null,null)
        return
      }
      embedding_task(img, function(err,result) {
        /* Format of result
          {
           "result":{
              "style":"front",
              "url":"http://aioss.tiegushi.com/2eecee88-ff24-11e8-a63a-0242ac140007",
              "face_fuzziness":389.8992707171606,
              "recognized":true,
              "detected":true,
              "face_id":"15380878754880000",
              "accuracy":97
           }
          }
        */
        //console.log(result)
        if(result.result.recognized && ONE_KNOWN_PERSON_BYPASS_QUEUE_MODE){
          recognized_results.push(result)
          callback(null,result)
          return
        }
        callback(null,result)
      })
    }, function(err, results){
      if(err){
        console.log('Error in Embedding Task')
        console.log(err)
        return cb && cb(err,null)
      } else {
        return cb && cb(null,results)
        if(ONE_KNOWN_PERSON_BYPASS_QUEUE_MODE && recognized_results.length>0){
          callback(null,recognized_results)
          return
        } else {
          cb(null,results)
        }
      }
    });

  },
  embedding_clustering : function(cropped_images, trackerId, cb) {
    var index = 0;
    var recognized_results=[];

    async.mapLimit(cropped_images,CLUSTER_CONCURRENCY,function(img,callback){
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
      if(ONE_KNOWN_PERSON_BYPASS_QUEUE_MODE && recognized_results.length>0){
        console.log('skipped in bypass mode, recognized_results ',recognized_results)
        callback(null,null)
        return
      }
      embedding_only_task(img, function(err,result) {
        //console.log('embedding_path: ',result.embedding_path)
        if(result.result.recognized && ONE_KNOWN_PERSON_BYPASS_QUEUE_MODE){
          recognized_results.push(result)
          callback(null,result)
          return
        }
        callback(null,result)
      })
    }, function(err, results){
      if(err){
        console.log('Error in Embedding Task')
        console.log(err)
        return cb && cb(err,null)
      } else {
        return cb && cb(null,results)
        if(ONE_KNOWN_PERSON_BYPASS_QUEUE_MODE && recognized_results.length>0){
          callback(null,recognized_results)
          return
        } else {
          cb(null,results)
        }
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
    },celery_task_expires_option());
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
    },celery_task_expires_option());
  } else {
    console.log('Abnormal situation, not connected to celery broker. Please check this')
    return cb && cb('error', 0, null)
  }
}

function embedding_task(cropped_file_path, cb) {
  if(connected_to_celery_cluster){
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
    },celery_task_expires_option());
  } else {
    console.log('Abnormal situation, not connected to celery cluster. Please check this')
    return cb && cb('error', null)
  }
}
function classify_task(task_info, cb) {
  if(connected_to_celery_broker){
    client.call('classify.classify',
      [task_info],
      function(result){
        ON_DEBUG && console.log(result)
        if(result && result.status === 'SUCCESS'){
          if(result.result){
            var json = JSON.parse(result.result)
            console.log('JSON.parse(result.result)=',json)
            json.result['url'] = upload.getAccessUrl(json.result.key)
            console.log('json.result.key[',json.result.key,']task_info.path',task_info.path)
            var key = json.result.key
            upload.putFile(key,task_info.path,function(error,accessUrl){
              console.log('error=',error,'accessUrl=',accessUrl)
              if(!error){
                var gst_api_url = json.api_data.api_url
                var json_request_content = json.api_data.payload
                json_request_content.img_url = accessUrl
                console.log('api_url,',gst_api_url,'json_request_content ',json_request_content)
                requestretry({
                    url: gst_api_url,
                    method: "POST",
                    json: true,
                    maxAttempts: 5,   // (default) try 5 times
                    retryDelay: 5000,
                    body: json_request_content
                }, function (error, response, body){
                    if(error) {
                        console.log("report to server event: ",error)
                    } else {
                        console.log('report to server event: ',body)
                        if(body && body.state=="SUCCESS" && body.result) {
                            var json = JSON.parse(body.result)
                        }
                    }
                });
              }
            })
            delete json.result.key
            console.log('classify result json:',json)
            return cb && cb(null, json)
          }
        }
        return cb && cb('error', null)
    },celery_task_expires_option());
  } else {
    console.log('Abnormal situation, not connected to celery broker. Please check this')
    return cb && cb('error', null)
  }
}
function embedding_only_task(task_info, cb) {
  if(connected_to_celery_broker){
    var buff = fs.readFileSync(task_info.path);
    var base64data = buff.toString('base64');
    //console.log('Image converted to base 64 is:\n\n' + base64data);
    task_info.base64data = base64data;

    cluster_client.call('upload_api-v2.extract_v2',
      [task_info],
      function(result){
        ON_DEBUG && console.log(result)

        if(result && result.status === 'SUCCESS'){
          if(result.result){
            var json = JSON.parse(result.result)
            ON_DEBUG && console.log(json)
            var embedding_tmp_path = task_info.path+'.txt'
            fs.writeFileSync(embedding_tmp_path,json.embedding_str);
            task_info.embedding_path = embedding_tmp_path
            delete task_info.base64data
            return classify_task(task_info,cb)
            //return cb && cb(null, json)
          }
        }
        return cb && cb('error', null)
    },celery_task_expires_option());
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

    fs.readFile(DEVICE_UUID_FILEPATH, 'utf8', function(err, data){
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
  fs.readFile(DEVICE_UUID_FILEPATH, function (err,data) {
    if (err) {
      return cb && cb('no_uuid')
    }
    return cb && cb(data.toString().replace(/(\r\n\t|\n|\r\t)/gm,""))
  });
}

function get_device_group_id(cb){
    fs.readFile(DEVICE_GROUP_ID_FILEPATH, function (err,data) {
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
