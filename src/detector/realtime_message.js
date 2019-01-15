var mqtt = require('mqtt')
var redis = require("redis")
var request = require('requestretry')
var brokerhost = process.env.BROKERHOST || 'mqtt://broker'
var client  = mqtt.connect(brokerhost)
var ON_DEBUG = false
function GetEnvironmentVarInt(varname, defaultvalue)
{
    var result = process.env[varname];
    if(result!=undefined)
        return parseInt(result,10);
    else
        return defaultvalue;
}


// 通过环境变量来控制重发消息机制
var THRESHOLD_ON_REALTIME_MESSAGE = GetEnvironmentVarInt('THRESHOLD_ON_REALTIME_MESSAGE', 0)


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
})

var MESSAGE_THRESHOLD = 30
var redisClient = null
if(!THRESHOLD_ON_REALTIME_MESSAGE){
  redisClient = redis.createClient(
      {port: 6379,
          return_buffers: true, // to handle binary payloads
          host: process.env.REDIS_HOST || "redis",
          password:   process.env.REDIS_PASSWORD});

  redisClient.select(15, function() {
    console.log('select database 15 to avoid conflict')
  });
}

// callback true to allow send
// callback false to disallow send
function message_threshold_check(person_id,cb){
    if(!THRESHOLD_ON_REALTIME_MESSAGE){
      if(cb){
        cb(true)
      }
      return
    }
    var my_key='key_limit_'+person_id;
    redisClient.exists(my_key,function(err,res){
      ON_DEBUG && console.log('begin redis return =  ===================')
      ON_DEBUG && console.log(err)
      ON_DEBUG && console.log(res)
      if(err){
          //Error to operate redis, need send all
          ON_DEBUG && console.log('need send person message:'+person_id)
          if(cb){
              cb(true)
          }
          return
      }
      // Can Send
      if(!res){
          redisClient.set(my_key,1,function(){
            redisClient.expire(my_key,MESSAGE_THRESHOLD,function(){
              ON_DEBUG && console.log('expire my key')
            })
          })
          if(cb){
            cb(true);
          }
      } else {
        redisClient.ttl(my_key,function(err,res){
          if(res === -1){
            redisClient.expire(my_key,MESSAGE_THRESHOLD,function(){
              ON_DEBUG && console.log('set expire my key to '+MESSAGE_THRESHOLD)
            })
            if(cb){
              cb(true);
            }
          } else {
            cb();
          }
          ON_DEBUG && console.log('expire in '+res)
        })
      }

      ON_DEBUG && console.log('end redis return =  ===================')
    });
};

function post_stranger_pushnotification(person_id, persons) {
    var unknown_url = 'http://workaihost.tiegushi.com/restapi/workai_unknown';
    var return_json = {"person_id":person_id, "persons": persons.concat()}

    request({
        url: unknown_url,
        method: "POST",
        json: true,
        maxAttempts: 5,   // (default) try 5 times
        retryDelay: 5000,
        headers: {
        "content-type": "application/json",
        },
        body: return_json
    }, function (error, response, body){
        if(error) {
            console.log("/restapi/workai_unknown ",error)
        } else {
            if(body && body.state=="SUCCESS" && body.result) {
                var json = JSON.parse(body.result)
            }
        }
    });
}

module.exports = {
  send_rt_unknown_message: function(info){
    ON_DEBUG && console.log(JSON.stringify(info))
    message_threshold_check('unknown',function(res){
      if(res){
        client.publish('rt_message', JSON.stringify(info))
        post_stranger_pushnotification(info.person_id, info.persons)
      }
    })
  },
  send_rt_known_message: function(info){
    ON_DEBUG && console.log(JSON.stringify(info))
    message_threshold_check(info.person_id,function(res){
      if(res){
        client.publish('rt_message', JSON.stringify(info))
        post_stranger_pushnotification(info.person_id, info.persons)
      }
    })
  }
}
