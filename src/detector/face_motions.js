
var fs = require('fs')
var path = require('path')
var mkdirp = require('mkdirp')
var mv = require('mv')
var request = require('requestretry')
var readdir = require('readdir-absolute')
const TelegramBot = require('node-telegram-bot-api');

const limiter = require('limiter')

var makegif=require('./makegif')
var upload=require('./upload')
var timeline=require('./timeline')
var mqttgif=require('./mqttgif')
var FACE_MOTION_REPORT_SERVER_REQUEST_PREFIX = 'http://timealbumemail.tiegushi.com/timelines/add?'

//var FACE_MOTION_REPORT_SERVER_REQUEST_PREFIX = 'http://10.5.52.253:3000/timelines/add?'
var REPORT_FACE_MOTION_TO_EVENT_SERVER = true

var DEVICE_UUID_FILEPATH = process.env.DEVICE_UUID_FILEPATH || '/dev/ro_serialno'
var DEVICE_GROUP_ID_FILEPATH = process.env.DEVICE_GROUP_ID_FILEPATH || '/data/usr/com.deep.workai/cache/groupid.txt'
var MQTT_BROKER_ADDRESS = process.env.MQTT_BROKER_ADDRESS || 'mqttbroker'

var ON_DEBUG = false

// replace the value below with the Telegram token you receive from @BotFather
var telegram_bot = null;
var telegram_chat_id = null;
const rate_limiter = new limiter.RateLimiter({
  tokensPerInterval: 1,
  interval: "minute"
});
const mqtt_rate_limiter = new limiter.RateLimiter({
  tokensPerInterval: 1,
  interval: "minute"
});

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

var MQTT_PORT = GetEnvironmentVarInt('MQTT_BROKER_PORT', 1883)
var mqtt_server = 'mqtt://' + MQTT_BROKER_ADDRESS + ':' + MQTT_PORT

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
  if(trackerId != '' || trackerId != null){
    try{
      makegif.removeUnusedImageDir(saving_path, 'face_motion/')
    } catch(error){
      console.error(error)
    }
  }
}

var mqtt = require('mqtt')
var client  = mqtt.connect(mqtt_server)
client.on('connect', function () {
  client.subscribe('presence', function (err) {
    if (!err) {
      client.publish('presence', 'Hello mqtt')
    }
  })
})

client.on('message', function (topic, message) {
  // message is Buffer
  ON_DEBUG && console.log(message.toString())
  var json_str = message.toString()
  ON_DEBUG && console.log('json string: ', json_str)
  try{
    var json = JSON.parse(json_str)
    if (json.type == 'text' && json.text ){
      if (mqtt_rate_limiter.tryRemoveTokens(1)){
        send_text_to_telegram(json.text)
      } else{
        return 
      }
    }
  } catch(a){
    return
  }
})

var interval_handler = setInterval(function(){
  get_device_uuid(function(uuid){
    get_device_group_id(function(group_id){
      if(uuid && group_id){
        clearInterval(interval_handler)
        var msg_topic = '/msg/g/' + group_id
        client.subscribe(msg_topic, function (err) {
          if (!err) {
            send_text_to_telegram('subscribed to group:'+group_id)
          }
        })
      }
    })
  })
},10000)



function send_image_to_telegram(image_path){
  if(telegram_bot == null || telegram_chat_id == null){
    return false
  }
  telegram_bot.sendPhoto(telegram_chat_id, image_path)
}
function send_video_to_telegram(video_path){
  if(telegram_bot == null || telegram_chat_id == null){
    return false
  }
  telegram_bot.sendVideo(telegram_chat_id, video_path)
}
function send_text_to_telegram(text){
  if(telegram_bot == null || telegram_chat_id == null){
    return false
  }

  telegram_bot.sendMessage(telegram_chat_id, text);
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
    if (rate_limiter.tryRemoveTokens(1)){
      ON_DEBUG && console.log('Tokens removed');
    } else{
      ON_DEBUG && console.log('No tokens removed >>>>>>>>>>>>>>>> threshold not call genvideo');
      return cb && cb(null,whole_file)
    }
    makegif.generateVideo('jpg',saving_path,name_sorting,function(err,gif_path,files){
      if(!err && gif_path){
        ON_DEBUG && console.log('Generated gif, need upload: '+gif_path)

        send_video_to_telegram(gif_path)
        return cb && cb(null,whole_file)
        
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
                          console.log('pop up gif images...')
                          /* total people >=2 and >=1 people is not recognized*/
                          // if(number >= 2) {
                          //   if(images && images.length > 0) {
                          //     mqttgif.post_stranger_gif_4_label('unknown',trackerId, cameraId, url,uuid,group_id,images,peoplenum)
                          //   }
                          // }
                        })
                      }
                      send_face_motion_event_to_event_server(group_id,uuid,face_ids,cameraId,url)
                    } else {
                      insert2timelineDB(files, trackerId, uuid, group_id, number, 0, function(){});
                      if(front_faces>2){
                        console.log('Unfamiliar faces event')
                        send_face_motion_event_to_event_server(group_id,uuid,'unknown',cameraId,url)
                        getAllFilesResults(files, trackerId, function(err, images, peoplenum) {
                          console.log('pop up all gif images...')
                          // if(images && images.length > 0) {
                          //   mqttgif.post_stranger_gif_4_label('unknown',trackerId, cameraId, url,uuid,group_id,images, peoplenum)
                          // }
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
function init_face_motion(options){
  token = options.telegram_bot_token
  if (token == null){
    console.log('no token for telegram bot')
    return
  }
  console.log('telegram token is', token)
  // Create a bot that uses 'polling' to fetch new updates
  telegram_bot = new TelegramBot(token, {polling: true});

  // Matches "/echo [whatever]"
  telegram_bot.onText(/\/start (.+)/, (msg, match) => {
    // 'msg' is the received Message from Telegram
    // 'match' is the result of executing the regexp above on the text content
    // of the message

    const chatId = msg.chat.id;
    telegram_chat_id = chatId;
    console.log('chat Id is: '+chatId);
    const resp = 'DeepCamera is running'; 

    telegram_bot.sendMessage(chatId, resp);
  });

  // Listen for any kind of message. There are different kinds of
  // messages.
  telegram_bot.on('message', (msg) => {
    const chatId = msg.chat.id;
    telegram_chat_id = chatId;

    // send a message to the chat acknowledging receipt of their message
    telegram_bot.sendMessage(chatId, 'Received your message');
  });
}
module.exports = {
  // Only generate gif if saved image === 19 or stopped(face_detected === 0).
  clean_up_face_motion_folder : remove_face_motion_images,
  init : init_face_motion,
  check_and_generate_face_motion_gif :function (face_detected,cameraId,trackerId,whole_file,name_sorting,cb){
    get_number_of_face_motion_saved_images('jpg',cameraId,trackerId,function(num){
      if(face_detected === 0){
        ON_DEBUG && console.log('end of current tracker id logic')
        if(num === 0){
          ON_DEBUG && console.log('stop check: no face detected, Just need remove folder')
          remove_face_motion_images(cameraId,trackerId)
        } else if(num >= 200){
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
        if(num === 199){
          ON_DEBUG && console.log('In time bingo: 19 face motion images saved, save/generate/upload/report ')
          return do_generate_gif_and_upload(cameraId,trackerId,whole_file,name_sorting,cb)
        } else if(num < 199){
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
        if(item[j]){
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
