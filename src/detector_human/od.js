//'use strict'

var Canvas = require('canvas');
var moment = require('moment');
var config=require('./conf.json');
var deepeye = require('./deepeye')

var s={
    group:{},
    has_motion:false
}
var ON_DEBUG = false
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
        var has_motion = false;
        d.width  = d.image.width;
        d.height = d.image.height;
        if(!s.group[d.ke][d.id].canvas[cord.name]){
            if(!cord.sensitivity||isNaN(cord.sensitivity)){
                cord.sensitivity = d.mon.detector_sensitivity;
            }
            s.group[d.ke][d.id].canvas[cord.name] = new Canvas(d.width,d.height);
            s.group[d.ke][d.id].canvasContext[cord.name] = s.group[d.ke][d.id].canvas[cord.name].getContext('2d');
            s.group[d.ke][d.id].canvasContext[cord.name].fillStyle = '#005337';
            s.group[d.ke][d.id].canvasContext[cord.name].fillRect( 0, 0,d.width,d.height);
            if(cord.points&&cord.points.length>0){
                s.group[d.ke][d.id].canvasContext[cord.name].beginPath();
                for (var b = 0; b < cord.points.length; b++){
                    cord.points[b][0]=parseFloat(cord.points[b][0]);
                    cord.points[b][1]=parseFloat(cord.points[b][1]);
                    if(b===0){
                        s.group[d.ke][d.id].canvasContext[cord.name].moveTo(cord.points[b][0],cord.points[b][1]);
                    }else{
                        s.group[d.ke][d.id].canvasContext[cord.name].lineTo(cord.points[b][0],cord.points[b][1]);
                    }
                }
                s.group[d.ke][d.id].canvasContext[cord.name].clip();
            }
        }
        if(!s.group[d.ke][d.id].canvasContext[cord.name]){
           return
        }
        s.group[d.ke][d.id].canvasContext[cord.name].drawImage(d.image, 0, 0, d.width, d.height);
        if(!s.group[d.ke][d.id].blendRegion[cord.name]){
            s.group[d.ke][d.id].blendRegion[cord.name] = new Canvas(d.width, d.height);
            s.group[d.ke][d.id].blendRegionContext[cord.name] = s.group[d.ke][d.id].blendRegion[cord.name].getContext('2d');
        }
        var sourceData = s.group[d.ke][d.id].canvasContext[cord.name].getImageData(0, 0, d.width, d.height);
        // create an image if the previous image doesn�t exist
        if (!s.group[d.ke][d.id].lastRegionImageData[cord.name]) s.group[d.ke][d.id].lastRegionImageData[cord.name] = s.group[d.ke][d.id].canvasContext[cord.name].getImageData(0, 0, d.width, d.height);
        // create a ImageData instance to receive the blended result
        var blendedData = s.group[d.ke][d.id].canvasContext[cord.name].createImageData(d.width, d.height);
        // blend the 2 images
        s.differenceAccuracy(blendedData.data,sourceData.data,s.group[d.ke][d.id].lastRegionImageData[cord.name].data);
        // draw the result in a canvas
        s.group[d.ke][d.id].blendRegionContext[cord.name].putImageData(blendedData, 0, 0);
        // store the current webcam image
        s.group[d.ke][d.id].lastRegionImageData[cord.name] = sourceData;
        blendedData = s.group[d.ke][d.id].blendRegionContext[cord.name].getImageData(0, 0, d.width, d.height);
        var i = 0;
        var average = 0;
        while (i < (blendedData.data.length * 0.25)) {
            average += (blendedData.data[i * 4] + blendedData.data[i * 4 + 1] + blendedData.data[i * 4 + 2]);
            ++i;
        }
        average = (average / (blendedData.data.length * 0.25))*10;

        if(!cord.sensitivity||isNaN(cord.sensitivity)){
            cord.sensitivity = d.mon.detector_sensitivity;
        }
        if (average > parseFloat(cord.sensitivity)){
        //if (average > 30){
            s.cx({f:'trigger',id:d.id,ke:d.ke,details:{plug:config.plug,name:cord.name,reason:'motion',confidence:average}})
            ON_DEBUG && console.log('Has motion, average: ' + average)
            has_motion = true;
            //post2workaipython(d, average);
        } else {
            ON_DEBUG && console.log('Sensitivity is ' + parseFloat(cord.sensitivity) + ' average is ' + average);
            has_motion = false;
        }
        s.group[d.ke][d.id].canvasContext[cord.name].clearRect(0, 0, d.width, d.height);
        s.group[d.ke][d.id].blendRegionContext[cord.name].clearRect(0, 0, d.width, d.height);

        return has_motion;
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
      s.image = new Canvas.Image;

      if(d.mon.detector_scale_x===''||d.mon.detector_scale_y===''){
          s.systemLog('Must set detector image size')
          return
      }else{
          s.image.width=d.mon.detector_scale_x;
          s.image.height=d.mon.detector_scale_y;
      }
      //ON_DEBUG && console.log('to load')
      s.image.onload = function() {
          //ON_DEBUG && console.log('onload')

          deepeye.saveCanvas2png(d.id, s.image,function(err, filepath){
            s.image.src = null
            if(!err && filepath){

              //Only Do Motion Detection when wanted. Can configure on GUI.
              if(need_detect_motion){
                //s.has_motion = s.checkAreas(d);
                ON_DEBUG && console.log('calling object detection...')
                deepeye.object_detection(d.id, filepath,function(err,person_count){
                  ON_DEBUG && console.log('finished object detection')
                  ON_DEBUG && console.log(err)
                  ON_DEBUG && console.log(result)

                  s.person_count = person_count
                  if(person_count>0){
                    ON_DEBUG && console.log('has person')
                    s.has_motion = true
                  } else {
                    s.has_motion = false
                  }
                  onframe(d.id, s.has_motion,filepath,person_count)
                })
              } else {
                onframe(d.id, s.has_motion,filepath,s.person_count)
              }
            } else {
              console.log('Need check the error of deepeye.saveCanvas2png')
            }

          })
      }
      ON_DEBUG && console.log(s.group[d.ke][d.id].buffer.length)
      s.image.src = s.group[d.ke][d.id].buffer;
      s.group[d.ke][d.id].buffer=null;
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
                            handle_frame(d,false);
                            return
                        }else{
                            if(!d.mon.detector_lock_timeout||d.mon.detector_lock_timeout===''||d.mon.detector_lock_timeout==0){
                                d.mon.detector_lock_timeout=2000
                            }else{
                                d.mon.detector_lock_timeout=parseFloat(d.mon.detector_lock_timeout)
                            }
                            s.group[d.ke][d.id].motion_lock=setTimeout(function(){
                                clearTimeout(s.group[d.ke][d.id].motion_lock);
                                delete(s.group[d.ke][d.id].motion_lock);
                            },d.mon.detector_lock_timeout)

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
