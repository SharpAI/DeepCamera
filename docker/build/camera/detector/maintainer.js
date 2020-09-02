var Docker = require('dockerode')
var docker = new Docker({socketPath: '/var/run/docker.sock'})

var CORE_AI_DOCKER_NAME = 'flower'

var face_detector = docker.getContainer(CORE_AI_DOCKER_NAME)
var last_check_ts = null
var checked_times = 0
module.exports = {
  onError : function (type,error){
    if(type === 'face detection'){
      // query API for container info
      face_detector.inspect(function (err, data) {
        console.log(data);
        if(!err && data){
          var state = data.State
          if(state){
            console.log(state)
            if(state.Running){
              var diff = (Date.now() - Date.parse(state.StartedAt))/1000
              console.log(diff)
              if(diff > 300){
                if(!last_check_ts){
                  last_check_ts = Date.now()
                  checked_times = 0
                }

                if((Date.now() - last_check_ts) < 120*1000){
                  if(++checked_times > 10){
                    console.log('need restart docker ' + CORE_AI_DOCKER_NAME)
                    face_detector.restart()
                  }
                } else {
                  last_check_ts = Date.now()
                }
              }
            }
          }
        }
      });
    }
  }
}
