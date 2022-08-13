//'use strict'

var moment = require('moment');
var config=require('./conf.json');
var deepeye = require('./deepeye');

var s={
    group:{},
    has_motion:false
}
var ON_DEBUG = false
var old_time = new Date()
module.exports = {
  init : function(onframe){
    if(process.argv[2]&&process.argv[3]){
        config.host=process.argv[2]
        config.port=process.argv[3]
        config.key=process.argv[4]
    }
    if(config.systemLog===undefined){config.systemLog=true}

    s.systemLog=function(q,w,e){
        if(!w){w=''}
        if(!e){e=''}
        if(config.systemLog===true){
           return console.log(moment().format(),q,w,e)
        }
    }
    s.blenderRegion=function(d,cord){
    }
    function fastAbs(value) {
        return (value ^ (value >> 31)) - (value >> 31);
    }

    function threshold(value) {
        return (value > 0x15) ? 0xFF : 0;
    }

    function difference(target, data1, data2) {
        // blend mode difference
        if (data1.length != data2.length) return null;
        var i = 0;
        while (i < (data1.length * 0.25)) {
            target[4 * i] = data1[4 * i] == 0 ? 0 : fastAbs(data1[4 * i] - data2[4 * i]);
            target[4 * i + 1] = data1[4 * i + 1] == 0 ? 0 : fastAbs(data1[4 * i + 1] - data2[4 * i + 1]);
            target[4 * i + 2] = data1[4 * i + 2] == 0 ? 0 : fastAbs(data1[4 * i + 2] - data2[4 * i + 2]);
            target[4 * i + 3] = 0xFF;
            ++i;
        }
    }
    s.differenceAccuracy=function(target, data1, data2) {
        if (data1.length != data2.length) return null;
        var i = 0;
        while (i < (data1.length * 0.25)) {
            var average1 = (data1[4 * i] + data1[4 * i + 1] + data1[4 * i + 2]) / 3;
            var average2 = (data2[4 * i] + data2[4 * i + 1] + data2[4 * i + 2]) / 3;
            var diff = threshold(fastAbs(average1 - average2));
            target[4 * i] = diff;
            target[4 * i + 1] = diff;
            target[4 * i + 2] = diff;
            target[4 * i + 3] = 0xFF;
            ++i;
        }
    }

    s.checkAreas=function(d){
        if(!s.group[d.ke][d.id].cords){
            if(!d.mon.cords){d.mon.cords={}}
            s.group[d.ke][d.id].cords=Object.values(d.mon.cords);
        }
        if(d.mon.detector_frame==='1'){
            d.mon.cords.frame={name:'frame',s:d.mon.detector_sensitivity,points:[[0,0],[0,d.image.height],[d.image.width,d.image.height],[d.image.width,0]]};
            s.group[d.ke][d.id].cords.push(d.mon.cords.frame);
        }
        var has_motion = false;
        for (var b = 0; b < s.group[d.ke][d.id].cords.length; b++){
            if(!s.group[d.ke][d.id].cords[b]){return}
            if (s.blenderRegion(d,s.group[d.ke][d.id].cords[b])){
              has_motion = true;
            }
        }

        //delete(d.image)
        ON_DEBUG && console.log('Dont forget to delete image, has motion: '+has_motion)
        return has_motion
    }


    var io = require('socket.io-client')('ws://'+config.host+':'+config.port);//connect to master
    s.cx=function(x){x.pluginKey=config.key;x.plug=config.plug;return io.emit('ocv',x)}
    io.on('connect',function(d){
        s.cx({f:'init',plug:config.plug,notice:config.notice,type:config.type});
    })
    io.on('disconnect',function(d){
        io.connect();
    })
    var handle_frame = function(d,need_detect_motion){
      s.group[d.ke][d.id].buffer=Buffer.concat(s.group[d.ke][d.id].buffer);
      if((typeof d.mon.cords ==='string')&&d.mon.cords.trim()===''){
          d.mon.cords=[]
      }else{
          try{
              d.mon.cords=JSON.parse(d.mon.cords)
          }catch(err){
            //console.error(err)
          }
      }
      if(d.mon.detector_frame_save==="1"){
         d.base64=s.group[d.ke][d.id].buffer.toString('base64')
      }
      s.group[d.ke][d.id].cords=Object.values(d.mon.cords);
      d.mon.cords=d.mon.cords;
      d.image = {} //new Canvas.Image;

      if(d.mon.detector_scale_x===''||d.mon.detector_scale_y===''){
          s.systemLog('Must set detector image size')
          return
      }else{
          d.image.width=d.mon.detector_scale_x;
          d.image.height=d.mon.detector_scale_y;
      }
      //ON_DEBUG && console.log('to load')
      var start = new Date();
      //d.image.onload = function() {
          //ON_DEBUG && console.log('onload')
          var has_motion = false;

          //Only Do Motion Detection when wanted. Can configure on GUI.
          /*if(need_detect_motion){
            var start = new Date();
            s.has_motion = s.checkAreas(d);
            var end = new Date() - start;
            console.info("Execution time: %dms", end);
          }*/

          deepeye.buffer2file(d.id, s.group[d.ke][d.id].buffer,function(err, filepath){
            var end =  new Date();
            ON_DEBUG && console.log('cost: '+ (end-start));
            //d.image.src = null
            if(!err && filepath){
              s.has_motion = true
              var undefined_obj
              onframe(d.id, s.has_motion,filepath,undefined_obj,start)
            } else {
              console.log('Need check the error of deepeye.saveCanvas2png')
            }

            delete(d.image)
          })
      //}
      ON_DEBUG && console.log(s.group[d.ke][d.id].buffer.length)
      //d.image.src = s.group[d.ke][d.id].buffer;
      s.group[d.ke][d.id].buffer=null;
    }
    var handle_file = function(d){
      var start = new Date();
      s.has_motion = true
      var undefined_obj
      onframe(d.id, true,d.filename,undefined_obj,start)
    }
    io.on('f',function(d){
        switch(d.f){
            case'api_key':
                s.api_key=d.key;
                console.log('API Key from server is '+s.api_key);
            case'init_monitor':
                console.log('init_monitor');
                if(s.group[d.ke]&&s.group[d.ke][d.id]){
                    s.group[d.ke][d.id].canvas={}
                    s.group[d.ke][d.id].canvasContext={}
                    s.group[d.ke][d.id].blendRegion={}
                    s.group[d.ke][d.id].blendRegionContext={}
                    s.group[d.ke][d.id].lastRegionImageData={}
                    //tracker
                    s.group[d.ke][d.id].trackerid=null
                    s.group[d.ke][d.id].lastTimeStatmp=null

                    delete(s.group[d.ke][d.id].cords)
                    delete(s.group[d.ke][d.id].buffer)
                }
            break;
            case'file':
                try{
                    handle_file(d,true);
                }catch(err){
                    if(err){
                        s.systemLog(err)
                    }
                }
                break;
            case'frame':
                var time1=new Date().getTime()
                var time2=new Date().getTime()
                try{
                    if(!s.group[d.ke]){
                        s.group[d.ke]={}
                    }
                    if(!s.group[d.ke][d.id]){
                        s.group[d.ke][d.id]={
                            canvas:{},
                            canvasContext:{},
                            lastRegionImageData:{},
                            blendRegion:{},
                            blendRegionContext:{},
                        }
                    }
                    if(!s.group[d.ke][d.id].buffer){
                      s.group[d.ke][d.id].buffer=[d.frame];
                    }else{
                      s.group[d.ke][d.id].buffer.push(d.frame)
                    }
                    if(d.frame[d.frame.length-2] === 0xFF && d.frame[d.frame.length-1] === 0xD9){
                        if(s.group[d.ke][d.id].motion_lock){
                            ON_DEBUG && console.log('log on frame')
                            console.log('too fast, only in '+ (new Date() - old_time))
                            delete(s.group[d.ke][d.id].buffer)
                            //handle_frame(d,false);
                            return
                        }else{
                            if(!d.mon.detector_lock_timeout||d.mon.detector_lock_timeout===''||d.mon.detector_lock_timeout==0){
                                d.mon.detector_lock_timeout=2000
                            }else{
                                d.mon.detector_lock_timeout=parseFloat(d.mon.detector_lock_timeout)
                            }
                            d.mon.detector_lock_timeout=200
                            s.group[d.ke][d.id].motion_lock=setTimeout(function(){
                                clearTimeout(s.group[d.ke][d.id].motion_lock);
                                delete(s.group[d.ke][d.id].motion_lock);
                            },d.mon.detector_lock_timeout)

                            console.log('handle frame: '+ (new Date() - old_time))
                            old_time = new Date()
                            handle_frame(d,true);
                        }
                    }
                }catch(err){
                    if(err){
                        s.systemLog(err)

                        delete(s.group[d.ke][d.id].buffer)
                    }
                }
            break;
        }
    })

  }
}
