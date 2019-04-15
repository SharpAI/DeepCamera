
var fs = require('fs')
var path = require('path')
var mkdirp = require('mkdirp')
var mv = require('mv')
var request = require('requestretry')
var readdir = require('readdir-absolute')

var makegif=require('./makegif')
var upload=require('./upload')
var timeline=require('./timeline')
var mqttgif=require('./mqttgif')
var FACE_MOTION_REPORT_SERVER_REQUEST_PREFIX = 'http://timealbumemail.tiegushi.com/timelines/add?'

//var FACE_MOTION_REPORT_SERVER_REQUEST_PREFIX = 'http://10.5.52.253:3000/timelines/add?'
var REPORT_FACE_MOTION_TO_EVENT_SERVER = true

var DEVICE_UUID_FILEPATH = process.env.DEVICE_UUID_FILEPATH || '/dev/ro_serialno'
var DEVICE_GROUP_ID_FILEPATH = process.env.DEVICE_GROUP_ID_FILEPATH || '/data/usr/com.deep.workai/cache/groupid.txt'

var ON_DEBUG = false
function GetEnvironmentVarInt(varname, defaultvalue)
{
    var result = process.env[varname];
    if(result!=undefined)
        return parseInt(result,10);
    else
        return defaultvalue;
}
// ONE_KNOWN_PERSON_BYPASS_QUEUE_MODE 一张图里，出现一个人脸，不再计算后续
var GIF_UPLOADING = GetEnvironmentVarInt('GIF_UPLOADING', 1)

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
function remove_face_motion_images(cameraId,trackerId){
  var saving_path = 'face_motion/'+trackerId+'/'
  makegif.removeUnusedImageDir(saving_path, 'face_motion/')
}
function do_generate_gif_and_upload(cameraId,trackerId,whole_file,name_sorting,cb){

  save_face_motion_image(cameraId,trackerId,whole_file,function(error,file){
    if(error){
      console.log('>>>> ERROR on save_face_motion_image')
      return cb && cb('error',whole_file)
    }
    var saving_path = 'face_motion/'+trackerId+'/'
    var cropped_path = 'face_cropped/'+trackerId+'/'
    var file_key = cameraId+'_'+trackerId+'.gif'

    makegif.generateGif('jpg',saving_path,name_sorting,function(err,gif_path,files){
      if(!err && gif_path){
        ON_DEBUG && console.log('Generated gif, need upload: '+gif_path)
        upload.putFile(file_key,gif_path,function(err,url){
          if(!err){
            console.log('TODO: fill up information. Upload success, url is: ' + url)
            if(REPORT_FACE_MOTION_TO_EVENT_SERVER){
              get_device_uuid(function(uuid){
                get_device_group_id(function(group_id){

                  timeline.get_face_ids(trackerId,function(err,results,number,front_faces){
                    console.log('Got face ids in this animation')
                    if(!err && results.length > 0){
                      var face_ids = ''
                      var to_send_number = Math.min(results.length,number)
                      var recognized = [];
                      for(var i = 0; i < to_send_number; i++){
                        face_ids = face_ids + results[i][0] + ','
                        recognized.push(results[i][0])
                      }
                      insert2timelineDB(files, trackerId, uuid, group_id, number, to_send_number, function(){});

                      if(to_send_number < number){
                        if(front_faces>1){
                          face_ids = face_ids + 'unknown,'
                        }
                        getAllFilesResultsNotRecognized(files, trackerId, function(err, images, peoplenum) {
                          /* total people >=2 and >=1 people is not recognized*/
                          if(number >= 2) {
                            if(images && images.length > 0) {
                              mqttgif.post_stranger_gif_4_label('unknown',trackerId, cameraId, url,uuid,group_id,images,peoplenum)
                            }
                          }
                        })
                      }
                      send_face_motion_event_to_event_server(group_id,uuid,face_ids,cameraId,url)
                    } else {
                      insert2timelineDB(files, trackerId, uuid, group_id, number, 0, function(){});
                      if(front_faces>2){
                        console.log('Unfamiliar faces event')
                        send_face_motion_event_to_event_server(group_id,uuid,'unknown',cameraId,url)
                        getAllFilesResults(files, trackerId, function(err, images, peoplenum) {
                          if(images && images.length > 0) {
                            mqttgif.post_stranger_gif_4_label('unknown',trackerId, cameraId, url,uuid,group_id,images, peoplenum)
                          }
                        })
                      } else {
                        console.log('See some activity')
                        send_face_motion_event_to_event_server(group_id,uuid,'activity',cameraId,url)
                      }
                    }
                    //makegif.removeUnusedImageDir(saving_path, 'face_motion/');
                  })
                })
              })
            }
          } else {
            console.log('>>>> ERROR on upload.putFile')
            return cb && cb('>>>> ERROR on upload.putFile',whole_file)
          }

          return cb && cb(null,whole_file)
        })
      } else {
        console.log('>>>> ERROR on makegif.generateGif')
        console.log(err)
        console.log(gif_path)

        return cb && cb('>>>> ERROR on makegif.generateGif',whole_file)
      }
    })
  })
}

function get_face_motion_report_url(group_id,uuid,person_faceid,cameraId,file_url){
  return FACE_MOTION_REPORT_SERVER_REQUEST_PREFIX + 'img_url='+file_url+'&group_id='+
    group_id + '&uuid='+uuid+ '&faceid='+person_faceid+'&cameraId='+cameraId
}
function send_face_motion_event_to_event_server(group_id,uuid,person_name,cameraId,file_url){
  if(!GIF_UPLOADING){
    return;
  }
  var request_url =get_face_motion_report_url(group_id,uuid,person_name,cameraId,file_url)
  request({
      url: request_url,
      method: "GET",
      maxAttempts: 5,   // (default) try 5 times
      retryDelay: 5000
    }, function(error, response, body) {
    if(!error){
      console.log(request_url)
      console.log('Report Face Motion event done')
    } else {
      console.log('>>>> ERROR on request.get')
    }
  });
  //mqttgif.post_gif_2_group(person_name,file_url,uuid, group_id)
}

function get_number_of_face_motion_saved_images(type,cameraId,trackerId,cb){
  var saving_path = 'face_motion/'+trackerId+'/'
  readdir(saving_path,function(err,list){
    if(err){
      cb(0)
      return
    }
    var files = list.filter(function(element) {
      var extName = path.extname(element);
      return extName === '.'+type;
    })
    //console.log(files)
    cb(files.length)
  });
}

function save_face_motion_image_path(trackerId, filePath) {
  if(filePath === ''){
    return '';
  }

  var saving_path = 'face_motion/'+trackerId+'/'
  var filename = path.basename(filePath);
  var move_to_path = saving_path + filename

  return move_to_path;
}

function save_face_motion_image(cameraId,trackerId,filePath,cb){
  if(filePath === ''){
    return cb && cb(null, '')
  }
  var saving_path = 'face_motion/'+trackerId+'/'
  var move_to_path = save_face_motion_image_path(trackerId,filePath);

  mkdirp(saving_path, function (err) {
    if(ON_DEBUG){
      if (err) console.error(err)
      else console.log('pow!')
    }

    mv(filePath, move_to_path, function(err) {
      ON_DEBUG && console.log(err)
      return cb && cb(null, move_to_path)
    });
  });
}
module.exports = {
  // Only generate gif if saved image === 19 or stopped(face_detected === 0).
  clean_up_face_motion_folder : remove_face_motion_images,
  check_and_generate_face_motion_gif :function (face_detected,cameraId,trackerId,whole_file,name_sorting,cb){
    get_number_of_face_motion_saved_images('jpg',cameraId,trackerId,function(num){
      if(face_detected === 0){
        ON_DEBUG && console.log('end of current tracker id logic')
        if(num === 0){
          ON_DEBUG && console.log('stop check: no face detected, Just need remove folder')
          remove_face_motion_images(cameraId,trackerId)
        } else if(num >= 20){
          ON_DEBUG && console.log('stop check: already uploaded, Just need remove folder')
          remove_face_motion_images(cameraId,trackerId)
        } else if(num >= 1){
          ON_DEBUG && console.log('stop check: more than 1 saved, save/generate/upload/report/remove ')
          return do_generate_gif_and_upload(cameraId,trackerId,whole_file,name_sorting,function(){
            remove_face_motion_images(cameraId,trackerId)

            return cb && cb(null,whole_file)
          })
        }
      } else {
        ON_DEBUG && console.log('in tracking logic')
        if(num === 19){
          ON_DEBUG && console.log('In time bingo: 19 face motion images saved, save/generate/upload/report ')
          return do_generate_gif_and_upload(cameraId,trackerId,whole_file,name_sorting,cb)
        } else if(num < 19){
          // just save it for more incoming file
          return save_face_motion_image(cameraId,trackerId,whole_file,function(){
            return cb && cb(null,whole_file)
          })
        }
      }
      return cb && cb(null,whole_file)
    })
  },
  save_face_motion_image_path: save_face_motion_image_path
}

function getAllFilesResults(files, tracker_id, cb){
  timeline.pop_gif_info(tracker_id, files, true, function(err, info) {
    if(err)
      return cb && cb(err, null, 0);

    var ret_info = [];
    var max_peoplenum = 0;
    for(i=0;i<info.length;i++){
      var items = info[i].results;
      max_peoplenum = Math.max(max_peoplenum, info[i].peoplenum)

      for(j=0;j<items.length;j++) {
        var item = items[j].result;
        var img_info = {
              "faceid": item.face_id,
              "url": item.url,
              "img_type": "face",
              "accuracy": item.accuracy,
              "fuzziness": item.face_fuzziness,
              "sqlid": "0",
              "style": item.style
        }
        ret_info.push(img_info);
      }
    }
    return cb && cb(null, ret_info, max_peoplenum);
  });
}

function getAllFilesResultsNotRecognized(files, tracker_id, cb){
  timeline.pop_gif_info(tracker_id, files, true, function(err, info) {
    if(err)
      return cb && cb(err, null, 0);

    var ret_info = [];
    var max_peoplenum = 0;
    for(i=0;i<info.length;i++){
      max_peoplenum = Math.max(max_peoplenum, info[i].peoplenum)
      var items = info[i].results;
      for(j=0;j<items.length;j++) {
        var item = items[j].result;
        if(item.recognized == true)
            continue;

        var img_info = {
              "recognized": item.recognized,
              "faceid": item.face_id,
              "url": item.url,
              "img_type": "face",
              "accuracy": item.accuracy,
              "fuzziness": item.face_fuzziness,
              "sqlid": "0",
              "style": item.style
        }
        ret_info.push(img_info);
      }
    }
    return cb && cb(null, ret_info, max_peoplenum);
  });
}

function insert2timelineDB(files, tracker_id, uuid, group_id, totalpeople, recognized_num, cb){
  timeline.pop_gif_info(tracker_id, files, false, function(err, info) {
    if(err)
      return cb && cb(err, null, 0);
    var recognized_arr = [];
    var not_recognized_arr = [];

    //calculate recognized number
    for(i=0;i<info.length;i++) {
      var item = info[i].results;
      recognized_arr=[];
      not_recognized_arr=[];
      for(j=0;j<item.length;j++) {
        var item2 = item[j].result;
        item2.ts = info[i].ts
        item2.tid = tracker_id
        item2.uuid = uuid
        item2.group_id = '' + group_id
        if(item2.recognized == true) {
          recognized_arr.push(item2)
        }
        else {
          not_recognized_arr.push(item2)
        }
      }
      info[i].recognized = recognized_arr.length;
      info[i].recognized_arr = recognized_arr.concat();
      info[i].not_recognized_arr = not_recognized_arr.concat();
    }

    recognized_arr=[];
    not_recognized_arr=[];

    //sort by recognized number and total number
    function sortByNum(a, b) {
      return (a.peoplenum + a.recognized) < (b.peoplenum + b.recognized);
    }
    info.sort(sortByNum);

    //recognized_num=totalpeople  >> all recognized
    if(recognized_num >= totalpeople) {
      for(i=0;i<info.length;i++) {
        if(info[i].recognized > 0) {
            recognized_arr = info[i].recognized_arr.concat();
            break;
        }
      }
      not_recognized_arr = [];
    }
    //recognized=0  >> all not recognized
    else if(recognized_num == 0) {
      for(i=0;i<info.length;i++) {
        if(info[i].recognized == 0) {
            not_recognized_arr = info[i].not_recognized_arr.concat();
            break;
        }
      }
      recognized_arr = [];
    }
    else if(recognized_num > 0 && recognized_num < totalpeople) {
      for(i=0;i<info.length;i++) {
        if(info[i].recognized > 0) {
          recognized_arr = info[i].recognized_arr.concat();
          not_recognized_arr = info[i].not_recognized_arr.concat();
          break;
        }
      }
    }

    //save recognized & not_recognized info to timeline_db
    var all_info = [];
    if(recognized_arr.length > 0) {
      all_info = recognized_arr.concat();
    }
    if(not_recognized_arr.length > 0) {
      all_info = not_recognized_arr.concat(all_info);
    }

    timeline.push_timeline_info(all_info, function (err) {
        if(err)
            console.log(err)

        timeline.send_realtime_msg(function(err){})
    })

    return cb && cb(null, null, 0);
  });
}
