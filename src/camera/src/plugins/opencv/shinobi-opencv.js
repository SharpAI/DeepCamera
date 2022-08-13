//
// Shinobi - OpenCV Plugin
// Copyright (C) 2016-2025 Moe Alam, moeiscool
//
// # Donate
//
// If you like what I am doing here and want me to continue please consider donating :)
// PayPal : paypal@m03.ca
//
process.on('uncaughtException', function (err) {
    console.error('uncaughtException',err);
});
var fs=require('fs');
var cv=require('opencv');
var exec = require('child_process').exec;
var moment = require('moment');
var Canvas = require('canvas');
var config=require('./conf.json');
if(config.systemLog===undefined){config.systemLog=true}
s={
    group:{},
    dir:{
        cascades:__dirname+'/cascades/'
    },
    isWin:(process.platform==='win32')
}
//default stream folder check
if(!config.streamDir){
    if(s.isWin===false){
        config.streamDir='/dev/shm'
    }else{
        config.streamDir=config.windowsTempDir
    }
    if(!fs.existsSync(config.streamDir)){
        config.streamDir=__dirname+'/streams/'
    }else{
        config.streamDir+='/streams/'
    }
}
s.dir.streams=config.streamDir;
//streams dir
if(!fs.existsSync(s.dir.streams)){
    fs.mkdirSync(s.dir.streams);
}
s.gid=function(x){
    if(!x){x=10};var t = "";var p = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
    for( var i=0; i < x; i++ )
        t += p.charAt(Math.floor(Math.random() * p.length));
    return t;
};
s.findCascades=function(callback){
    var tmp={};
    tmp.foundCascades=[];
    fs.readdir(s.dir.cascades,function(err,files){
        files.forEach(function(cascade,n){
            if(cascade.indexOf('.xml')>-1){
                tmp.foundCascades.push(cascade.replace('.xml',''))
            }
        })
        s.cascadesInDir=tmp.foundCascades;
        callback(tmp.foundCascades)
    })
}
s.findCascades(function(){
    //get cascades
})
s.detectObject=function(buffer,d){
  var keys = Object.keys(d.mon.detector_cascades);
  if(d.mon.detector_lisence_plate==="1"){
      if(!d.mon.detector_lisence_plate_country||d.mon.detector_lisence_plate_country===''){
          d.mon.detector_lisence_plate_country='us'
      }
      d.tmpFile=s.gid(5)+'.jpg'
      if(!fs.existsSync(s.dir.streams)){
          fs.mkdirSync(s.dir.streams);
      }
      d.dir=s.dir.streams+d.ke+'/'
      if(!fs.existsSync(d.dir)){
          fs.mkdirSync(d.dir);
      }
      d.dir=s.dir.streams+d.ke+'/'+d.id+'/'
      if(!fs.existsSync(d.dir)){
          fs.mkdirSync(d.dir);
      }
      fs.writeFile(d.dir+d.tmpFile,buffer,function(err){
          if(err) return s.systemLog(err);
          exec('alpr -j -c '+d.mon.detector_lisence_plate_country+' '+d.dir+d.tmpFile,{encoding:'utf8'},(err, scan, stderr) => {
              if(err){
                  s.systemLog(err);
              }else{
                  try{
                      try{
                          scan=JSON.parse(scan)
                      }catch(err){
                          if(!scan||!scan.results){
                              return s.systemLog(scan,err);
                          }
                      }
                      if(scan.results.length>0){
                          scan.plates=[]
                          scan.mats=[]
                          scan.results.forEach(function(v){
                              v.candidates.forEach(function(g,n){
                                  if(v.candidates[n].matches_template)
                                    delete(v.candidates[n].matches_template)
                              })
                              scan.plates.push({coordinates:v.coordinates,candidates:v.candidates,confidence:v.confidence,plate:v.plate})
                              var width = Math.sqrt( Math.pow(v.coordinates[1].x - v.coordinates[0].x, 2) + Math.pow(v.coordinates[1].y - v.coordinates[0].y, 2));
                              var height = Math.sqrt( Math.pow(v.coordinates[2].x - v.coordinates[1].x, 2) + Math.pow(v.coordinates[2].y - v.coordinates[1].y, 2))
                              scan.mats.push({
                                x:v.coordinates[0].x,
                                y:v.coordinates[0].y,
                                width:width,
                                height:height,
                                tag:v.plate
                              })
                          })
                          tx({f:'trigger',id:d.id,ke:d.ke,details:{plug:config.plug,name:'licensePlate',reason:'object',matrices:scan.mats,confidence:d.average,imgHeight:d.mon.detector_scale_y,imgWidth:d.mon.detector_scale_x,frame:d.base64}})
                      }
                  }catch(err){
                      s.systemLog(scan,err);
                  }
              }
              exec('rm -rf '+d.dir+d.tmpFile,{encoding:'utf8'})
          })
      })
  }
  if(keys.length===0){return false}
  cv.readImage(buffer, function(err,im){
      if(err){console.log(err);return false;}
      var width = im.width();
      var height = im.height();

      if (width < 1 || height < 1) {
         throw new Error('Image has no size');
      }
      keys.forEach(function(v,n){
          im.detectObject(s.dir.cascades+v+'.xml',{}, function(err,mats){
              if(err){console.log(err);return false;}
              if(mats&&mats.length>0){
                  mats.forEach(function(v,n){
                      v.centerX=v.width/2
                      v.centerY=v.height/2
                      v.centerXnoParent=v.x+(v.width/2)
                      v.centerYnoParent=v.y+(v.height/2)
                  })
                  s.cx({f:'trigger',id:d.id,ke:d.ke,details:{plug:config.plug,name:v,reason:'object',matrices:mats,confidence:d.average,imgHeight:height,imgWidth:width,frame:d.base64}})
              }
          })
      })
  })
}
s.systemLog=function(q,w,e){
    if(!w){w=''}
    if(!e){e=''}
    if(config.systemLog===true){
       return console.log(moment().format(),q,w,e)
    }
}
s.blenderRegion=function(d,cord){
    d.width  = d.image.width;
    d.height = d.image.height;
    if(!s.group[d.ke][d.id].canvas[cord.name]){
        if(!cord.sensitivity||isNaN(cord.sensitivity)){
            cord.sensitivity=d.mon.detector_sensitivity;
        }
        s.group[d.ke][d.id].canvas[cord.name] = new Canvas(d.width,d.height);
        s.group[d.ke][d.id].canvasContext[cord.name] = s.group[d.ke][d.id].canvas[cord.name].getContext('2d');
        s.group[d.ke][d.id].canvasContext[cord.name].fillStyle = '#000';
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
    d.average = 0;
    while (i < (blendedData.data.length * 0.25)) {
        d.average += (blendedData.data[i * 4] + blendedData.data[i * 4 + 1] + blendedData.data[i * 4 + 2]);
        ++i;
    }
    d.average = (d.average / (blendedData.data.length * 0.25))*10;
    if (d.average > parseFloat(cord.sensitivity)){
          var buffer=s.group[d.ke][d.id].canvas[cord.name].toBuffer();
          if(d.mon.detector_use_detect_object==="1"){
              s.detectObject(buffer,d)
          }else{
              s.cx({f:'trigger',id:d.id,ke:d.ke,details:{plug:config.plug,name:cord.name,reason:'motion',confidence:d.average,frame:d.base64}})
          }
    }
    s.group[d.ke][d.id].canvasContext[cord.name].clearRect(0, 0, d.width, d.height);
    s.group[d.ke][d.id].blendRegionContext[cord.name].clearRect(0, 0, d.width, d.height);
}
function blobToBuffer (blob, cb) {
  if (typeof Blob === 'undefined' || !(blob instanceof Blob)) {
    throw new Error('first argument must be a Blob')
  }
  if (typeof cb !== 'function') {
    throw new Error('second argument must be a function')
  }

  var reader = new FileReader()

  function onLoadEnd (e) {
    reader.removeEventListener('loadend', onLoadEnd, false)
    if (e.error) cb(e.error)
    else cb(null, Buffer.from(reader.result))
  }

  reader.addEventListener('loadend', onLoadEnd, false)
  reader.readAsArrayBuffer(blob)
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
        d.mon.cords.frame={name:'FULL_FRAME',s:d.mon.detector_sensitivity,points:[[0,0],[0,d.image.height],[d.image.width,d.image.height],[d.image.width,0]]};
        s.group[d.ke][d.id].cords.push(d.mon.cords.frame);
    }
    for (var b = 0; b < s.group[d.ke][d.id].cords.length; b++){
        if(!s.group[d.ke][d.id].cords[b]){return}
        s.blenderRegion(d,s.group[d.ke][d.id].cords[b])
    }
    delete(d.image)
}

io = require('socket.io-client')('ws://'+config.host+':'+config.port);//connect to master
s.cx=function(x){x.pluginKey=config.key;x.plug=config.plug;return io.emit('ocv',x)}
io.on('connect',function(d){
    s.cx({f:'init',plug:config.plug,notice:config.notice});
})
io.on('disconnect',function(d){
    io.connect();
})
io.on('f',function(d){
    switch(d.f){
        case'refreshPlugins':
            s.findCascades(function(cascades){
                s.cx({f:'s.tx',data:{f:'detector_cascade_list',cascades:cascades},to:'GRP_'+d.ke})
            })
        break;
        case'readPlugins':
            s.cx({f:'s.tx',data:{f:'detector_cascade_list',cascades:s.cascadesInDir},to:'GRP_'+d.ke})
        break;
        case'init_monitor':
            if(s.group[d.ke]&&s.group[d.ke][d.id]){
                s.group[d.ke][d.id].canvas={}
                s.group[d.ke][d.id].canvasContext={}
                s.group[d.ke][d.id].blendRegion={}
                s.group[d.ke][d.id].blendRegionContext={}
                s.group[d.ke][d.id].lastRegionImageData={}
                delete(s.group[d.ke][d.id].cords)
                delete(s.group[d.ke][d.id].buffer)
            }
        break;
        case'frame':
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
                    }
                    s.group[d.ke][d.id].buffer=Buffer.concat(s.group[d.ke][d.id].buffer);
                    try{
                        d.mon.detector_cascades=JSON.parse(d.mon.detector_cascades)
                    }catch(err){
                        
                    }
                    if(d.mon.detector_frame_save==="1"){
                       d.base64=s.group[d.ke][d.id].buffer.toString('base64')
                    }
                    if(d.mon.detector_use_motion==="1"||d.mon.detector_use_detect_object!=="1"){
                        if((typeof d.mon.cords ==='string')&&d.mon.cords.trim()===''){
                            d.mon.cords=[]
                        }else{
                            try{
                                d.mon.cords=JSON.parse(d.mon.cords)
                            }catch(err){
                            }
                        }
                        s.group[d.ke][d.id].cords=Object.values(d.mon.cords);
                        d.mon.cords=d.mon.cords;
                        d.image = new Canvas.Image;
                        if(d.mon.detector_scale_x===''||d.mon.detector_scale_y===''){
                            s.systemLog('Must set detector image size')
                            return
                        }else{
                            d.image.width=d.mon.detector_scale_x;
                            d.image.height=d.mon.detector_scale_y;
                        }
                        d.width=d.image.width;
                        d.height=d.image.height;
                        d.image.onload = function() { 
                            s.checkAreas(d);
                        }
                        d.image.src = s.group[d.ke][d.id].buffer;
                    }else{
                        s.detectObject(s.group[d.ke][d.id].buffer,d)
                    }
                    s.group[d.ke][d.id].buffer=null;
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