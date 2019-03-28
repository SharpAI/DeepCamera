var fs = require('fs')
var Datastore = require('nedb')
var visit = require('./visit')
var rt_msg = require('./realtime_message')
var timelineDuration = 60*1000; //30s
var sent_ts_recognized = 0;
var sent_ts_not_recognized = 0;
var realtime_msg_interval = 30*1000;
function GetEnvironmentVarInt(varname, defaultvalue)
{
    var result = process.env[varname];
    if(result!=undefined)
        return parseInt(result,10);
    else
        return defaultvalue;
}
// DEEP_ANALYSIS_MODE true=允许队列缓存, false=不允许队列缓存
var REALTIME_STRANGER_SDK_MESSAGE = GetEnvironmentVarInt('REALTIME_STRANGER_SDK_MESSAGE',1)

if (typeof db_global === 'undefined'){
  db_global = new Datastore()
  console.log('init nedb global')
}

//save all gif info (jpg_local_path, jpg_url, results)
if (typeof db_global_gif === 'undefined'){
  db_global_gif = new Datastore()
  console.log('init nedb global for gif')
}

if (typeof db_global_timeline === 'undefined'){
  db_global_timeline = new Datastore()
  console.log('init nedb global for timeline')
}

var DEVICE_UUID_FILEPATH = process.env.DEVICE_UUID_FILEPATH || '/dev/ro_serialno'
var DEVICE_GROUP_ID_FILEPATH = process.env.DEVICE_GROUP_ID_FILEPATH || '/data/usr/com.deep.workai/cache/groupid.txt'

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
function get_timeline_info(startts, recognized, cb) {
    if(recognized) {
      db_global_timeline.find({'recognized': true, 'ts': {$gte: startts}}).sort({'ts': -1}).exec(function(err, docs) {
        if(err || !docs)
            return cb && cb(err, null);

        return cb && cb(null, docs)
      })
    }
    else {
      db_global_timeline.find({'recognized': false, 'ts': {$gte: startts}}).sort({'ts': -1}).exec(function(err, docs) {
        if(err || !docs)
            return cb && cb(err, null);

        return cb && cb(null, docs)
      })
    }
}
function generate_known_person_message(tracker_id,recognition_results){
  var result_info = {
    status:'known person',
    persons:[],
    person_id:''
  }
  get_device_uuid(function(uuid){
    get_device_group_id(function(group_id){
      recognition_results.forEach(function(item){
        if(!item){
          console.log('one empty item in recognition_results, might be skipped when has known person recognized')
          return
        }
        var result = item.result
        if(result && result.recognized === true && result.face_id ){
          var person_info = {
              "id":result.face_id,
              "uuid":uuid,
              "group_id":group_id.toString(),
              "img_url":result.url,
              "position":"",
              "type":"face",
              "current_ts":Date.now(),
              "accuracy":result.accuracy,
              "fuzziness":result.face_fuzziness,
              "sqlid":0,
              "style":result.style,
              "tid":tracker_id,
              //"img_ts":1537393971031,
              "p_ids":[]
          }
          result_info.person_id = result.face_id
          result_info.persons.push(person_info)
        }
      })
      console.log('=============================')
      rt_msg.send_rt_known_message(result_info)
    })
  })
}

function generate_unknown_person_message(tracker_id,recognition_results){
  var result_info = {
    status:'Stranger',
    persons:[],
    person_id:''
  }
  get_device_uuid(function(uuid){
    get_device_group_id(function(group_id){
      recognition_results.forEach(function(result){
        var person_info = {
            "id":result.face_id,
            "uuid":uuid,
            "group_id":group_id.toString(),
            "img_url":result.url,
            "position":"",
            "type":"face",
            "current_ts":Date.now(),
            "accuracy":result.accuracy,
            "fuzziness":result.face_fuzziness,
            "sqlid":0,
            "style":result.style,
            "tid":tracker_id,
            //"img_ts":1537393971031,
            "p_ids":[]
        }
        result_info.person_id = result.face_id
        result_info.persons.push(person_info)
        console.log('unknown message ',result)
      })
      console.log('=============================')
      rt_msg.send_rt_unknown_message(result_info)
    })
  })
}
module.exports = {
  update: function(tracker_id,event_type,number,recognition_results){
    //console.log()
    /*[ { result:
     { detected: true,
       style: 'right_side',
       face_id: '15240799848220000',
       recognized: false,
       accuracy: 0 } } ]
    */
    if(recognition_results && recognition_results.length > 0){
      var recognitions = []
      var unknown_faces = []
      var front_faces = 0
      recognition_results.forEach(function(item){
        if(item != undefined && item != null && item.result != undefined && item.result != null) {
          var result = item.result
          if(result && result.recognized === true && result.face_id ){
            recognitions.push(result.face_id)
          }
          if(result && result.recognized === false && result.style ==='front' /*|| result.style == 'left_side' || result.style ==='right_side'*/){
            front_faces++
            console.log(result)
            unknown_faces.push(result)
          }
        }
      })

      var recognized = false
      if(recognitions.length > 0){
        recognized = true
        generate_known_person_message(tracker_id,recognition_results)
      }
      if(REALTIME_STRANGER_SDK_MESSAGE){
        if(unknown_faces.length > 0){
          generate_unknown_person_message(tracker_id,unknown_faces)
        }
      }

      console.log('=====> update tracker_id ' + tracker_id +
        ' type '+ event_type + ' results: ' + recognition_results)
      db_global.findOne({_id:tracker_id},function(err,doc){
        if(!err){
          if(doc === null){
            var record = {
              _id:tracker_id,
              recognized: recognized,
              results:{},
              front_faces: front_faces,
              number: number,
              created_on:Date.now()
            }
            recognitions.forEach(function(recognized_face){
              record.results[recognized_face] = 1
            })
            db_global.insert(record)
          } else {
            recognitions.forEach(function(recognized_face){
              if(doc.results[recognized_face]){
                doc.results[recognized_face]++
              } else {
                doc.results[recognized_face] = 1
              }
              if(doc.number !== number){
                console.log('==========>>>>> TODO: face number changes, need reset tracker id to regenerate the gifs and report ...')
              }
              if(doc.number < number){
                db_global.update({_id:tracker_id},{$set:{number:number}})
              }

            })
            console.log(doc)
            front_faces = front_faces + doc.front_faces
            db_global.update({_id:tracker_id},{$set:{
              results:doc.results,
              front_faces:front_faces,
              recognized:(recognized||doc.recognized)
            }})
          }
        }
      })
    }
  },
  get_faces_detected:function(tracker_id,cb){
    db_global.findOne({_id:tracker_id},function(err,doc){
      if(!err && doc){
        return cb && cb(null,doc.number)
      } else {
        return cb && cb(null,0)
      }
    })
  },
  get_tracking_info:function(tracker_id,cb){
      db_global.findOne({_id:tracker_id},function(err,doc){
        if(!err && doc){
          return cb && cb(null,doc)
        } else {
          return cb && cb('error',null)
        }
      })
  },
  get_face_ids:function(tracker_id,cb){
    db_global.findOne({_id:tracker_id},function(err,doc){
      if(!err && doc ){
        var results = doc.results
        var sorted = visit(results)
        console.log(sorted)

        if(doc.recognized){
          return cb && cb(null,sorted, doc.number, doc.front_faces)
        } else {
          return cb && cb(null,[], doc.number, doc.front_faces)
        }
      }
      return cb && cb(null,[],0,0)
    })
  },
  push_gif_info: function(tracker_id, jpg_motion_path, result, ts, cb) {
    db_global_gif.findOne({_id: tracker_id, path: jpg_motion_path},function(err,doc){
      if(err)
        return cb && cb(err);

      if(doc === null){
        var item = {
          tid: tracker_id,
          results: result,
          peoplenum: result.length,
          path: jpg_motion_path,
          ts: ts,
          created_on: Date.now()
        }
        db_global_gif.insert(item)
        return cb && cb(null);
      }
      else {
        console.log('oops! something error !')
        return cb && cb('wrong insert');
      }
    })
  },
  pop_gif_info: function(tracker_id, jpg_motion_path_arr, remove, cb) {
    db_global_gif.find({tid: tracker_id, path: {$in: jpg_motion_path_arr}},function(err,docs){
      if(err)
        return cb && cb(err, []);

      if(remove)
        db_global_gif.remove({tid: tracker_id})
      return cb && cb(null, docs);
    })
  },
  push_timeline_info: function(records, cb) {
      if(!records || records.length <1)
          return cb && cb("invalid parameters");

      var startts = Date.now() - timelineDuration;

      db_global_timeline.insert(records)
      db_global_timeline.remove({'ts': {$lt: startts}})
      return cb && cb(null);
  },
  send_realtime_msg: function(cb) {
      get_timeline_info(sent_ts_recognized, true, function(err, docs){
        if(err || !docs)
          return

        if(docs && docs.length > 0) {
          var persons = [];
          for(i=0;i<docs.length;i++) {
            var item = docs[i];
            persons.push({'id': item.face_id,
               'uuid': item.uuid,
               'group_id': item.group_id,
               'img_url': item.url,
               'position': '',
               'type': 'face',
               'current_ts': Date.now(),
               'accuracy': item.accuracy,
               'fuzziness': item.face_fuzziness,
               'sqlid': 0,
               'style': item.style,
               'tid': item.tid,
               'img_ts': item.ts,
               'p_ids': []
               })
          }
          var msg = {"status": "known person", "persons": persons, "person_id": docs[0].face_id}
          sent_ts_recognized = Date.now() + realtime_msg_interval;
          if(docs[0] && docs[0].ts) {
            sent_ts_recognized = docs[0].ts + realtime_msg_interval;
          }
          //rt_msg.send_rt_known_message(msg)
        }
      })

      get_timeline_info(sent_ts_not_recognized, false, function(err, docs){
        if(err || !docs)
          return

        if(docs && docs.length > 0) {
          var persons = [];

          for(i=0;i<docs.length;i++) {
            var item = docs[i];
            persons.push({'id': item.face_id,
               'uuid': item.uuid,
               'group_id': item.group_id,
               'img_url': item.url,
               'position': '',
               'type': 'face',
               'current_ts': Date.now(),
               'accuracy': item.accuracy,
               'fuzziness': item.face_fuzziness,
               'sqlid': 0,
               'style': item.style,
               'tid': item.tid,
               'img_ts': item.ts,
               'p_ids': []
               })
          }

          var msg = {"status": "Stranger", "persons": persons, "person_id": docs[0].face_id}
          sent_ts_not_recognized = Date.now() + realtime_msg_interval;
          if(docs[0] && docs[0].ts) {
            sent_ts_not_recognized = docs[0].ts + realtime_msg_interval;
          }
          rt_msg.send_rt_unknown_message(msg)
        }
      })
  }
}
