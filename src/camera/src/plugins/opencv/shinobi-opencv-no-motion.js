//
// Shinobi - OpenCV Plugin
// Copyright (C) 2016-2025 Moe Alam, moeiscool
//
// # Donate
//
// If you like what I am doing here and want me to continue please consider donating :)
// PayPal : paypal@m03.a
//
process.on('uncaughtException', function (err) {
    console.error('uncaughtException',err);
});
var fs=require('fs');
var cv=require('opencv');
var exec = require('child_process').exec;
var moment = require('moment');
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
s.systemLog=function(q,w,e){
    if(!w){w=''}
    if(!e){e=''}
    if(config.systemLog===true){
       return console.log(moment().format(),q,w,e)
    }
}
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
                      s.systemLog(err);
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
                  s.cx({f:'trigger',id:d.id,ke:d.ke,details:{plug:config.plug,name:v,reason:'object',matrices:mats,confidence:d.average,imgHeight:height,imgWidth:width}})
              }
          })
      })
  })
}
io = require('socket.io-client')('ws://'+config.host+':'+config.port);//connect to master
s.cx=function(x){x.pluginKey=config.key;x.plug=config.plug;return io.emit('ocv',x)}
io.on('connect',function(d){
    s.cx({f:'init',plug:config.plug});
})
io.on('disconnect',function(d){
    io.connect()
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
            d.details={}
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
                    s.group[d.ke][d.id].buffer=Buffer.concat(s.group[d.ke][d.id].buffer);
                    s.detectObject(s.group[d.ke][d.id].buffer,d)
                    s.group[d.ke][d.id].buffer=null;
                }
            } catch(err){
                    console.error(err)
                }
        break;
    }
})