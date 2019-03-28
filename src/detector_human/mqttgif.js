var http = require('http');
var request = require('requestretry')
var host = 'http://workaihost.tiegushi.com/'
gst_api_url = host + 'restapi/workai'
gst_stranger_api_url = host + 'restapi/updateStrangers'

function GetEnvironmentVarInt(varname, defaultvalue)
{
    var result = process.env[varname];
    if(result!=undefined)
        return parseInt(result,10);
    else
        return defaultvalue;
}
// ONE_KNOWN_PERSON_BYPASS_QUEUE_MODE 一张图里，出现一个人脸，不再计算后续
var SENDTOTIMELINE = GetEnvironmentVarInt('GIF_UPLOADING', 1)

function post_gif_2_group(faceid, url,uuid,group_id){
    if(!SENDTOTIMELINE) {
      return;
    }
    type = 'front'
    if(faceid == 'box'){
        type = 'image'
    }
    var json_request_content = {'id': faceid,
               'uuid': uuid,
               'group_id': group_id,
               'img_url': url,
               'position': 'face',
               'type': type,
               'current_ts': (new Date().getTime()),
               'accuracy': 1,
               'fuzziness': 50,
               'sqlid': 1,
               'style': 'front',
               'tid': faceid,
               'img_ts': '',
               'p_ids': [],
               'event_type': 'motion',
               'waiting': false
               }

    request({
        url: gst_api_url,
        method: "POST",
        json: true,
        maxAttempts: 5,   // (default) try 5 times
        retryDelay: 5000,
        body: json_request_content
    }, function (error, response, body){
        if(error) {
            console.log("mqtt-----error: ",error)
        } else {
            console.log('mqtt------body: ',body)
            if(body && body.state=="SUCCESS" && body.result) {
                var json = JSON.parse(body.result)
            }
        }
    });
}

function post_stranger_gif_4_label(faceid, trackerId, cameraId, gif_url, uuid, group_id, pic_arr, peoplenum){
    console.log('POST STRANGER INFO TO SERVER...')
    var images2lable = [];
    if(peoplenum >= 2) {
      images2lable.push(pic_arr[0]);
    }
    else {
      images2lable = pic_arr;
    }

    var json_request_content = {
        'imgs': images2lable,
        'img_gif': gif_url,
        'group_id': '' + group_id,
        'camera_id': cameraId,
        'uuid': uuid,
        'tid': trackerId,
        'isStrange': true,
        'createTime': new Date()}

    request({
        url: gst_stranger_api_url,
        method: "POST",
        json: true,
        maxAttempts: 5,   // (default) try 5 times
        retryDelay: 5000,
        headers: {
        "content-type": "application/json",
        },
        body: json_request_content
    }, function (error, response, body){
        if(error) {
            console.log("stranger---error: ",error)
        } else {
            console.log('stranger---body: ',body)
            if(body && body.state=="SUCCESS" && body.result) {
                var json = JSON.parse(body.result)
            }
        }
    });
}

module.exports = {
  post_gif_2_group : post_gif_2_group,
  post_stranger_gif_4_label : post_stranger_gif_4_label
}
