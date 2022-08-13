//
// Shinobi - Microsoft Computer Vision Plugin
// Copyright (C) 2016-2025 Moe Alam, moeiscool
//
process.on('uncaughtException', function (err) {
    console.error('uncaughtException',err);
});
var fs=require('fs');
var exec = require('child_process').exec;
//var http = require('http');
var request = require('request');
var moment = require('moment');
var cognitive = require('cognitive-services');
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
s.objectToParameter = function(obj){
    return Object.keys(obj).map(function(key) {
        return key + '=' + encodeURIComponent(obj[key]);
    }).join('&');
}
s.sendImageToMS=function(sourceImageUrl,API,callback){
    var URL = API.endpoint+'?'+s.objectToParameter(API.params)
    request(URL,{
        method: 'POST',
        headers:{
            "Ocp-Apim-Subscription-Key":API.apiKey
        },
        json: {
          url:sourceImageUrl
        }
    }, callback)
}
s.detectObject=function(buffer,d){
    var sourceImageUrl = 'http://184.105.6.43/'+s.api_key+'/jpeg/'+d.ke+'/'+d.id+'/s.jpg'
//    const client = new cognitive.computerVision({
//        apiKey: config.computerVision.apiKey,
//        endpoint: config.computerVision.endpoint
//    });
//    const parameters = {
//        "visualFeatures": "Categories,Tags,Description",
//        "details": "Celebrities,Landmarks"
//    };
//    const headers = {
//        'Content-type': 'application/json'
//    };
//    const body = {
//        "url": sourceImageUrl
//    };
//
//    client.analyzeImage({
//        parameters,
//        headers,
//        body
//    }).then((response) => {
////        should(response).not.be.undefined();
////        should(response).have.properties(["categories", "metadata", "requestId"]);
//        console.log(response)
//    }).catch((err) => {
//        console.log('Error',err)
//    });
    var responses = {}
    s.sendImageToMS(sourceImageUrl,config.computerVision,function(err,resp,body1){
        responses.computerVisionURL = body1
        s.sendImageToMS(sourceImageUrl,config.FaceAPI,function(err,resp,body2){
            responses.faceApiURL = body2
            s.sendImageToMS(sourceImageUrl,config.EmotionAPI,function(err,resp,body3){
                responses.EmotionAPI = body3
                console.log('responses',JSON.stringify(responses,null,3))
            })
        })
    })
}
s.makeMonitorObject=function(d){
    if(!s.group[d.ke]){
        s.group[d.ke]={}
    }
    if(!s.group[d.ke][d.id]){
        s.group[d.ke][d.id]={
            port:null,
            countStarted:new Date()
        }
    }
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
        case'api_key':
            s.api_key=d.key
        break;
        case'init_monitor':
            if(s.group[d.ke]&&s.group[d.ke][d.id]){
                s.group[d.ke][d.id].buffer=null
                s.group[d.ke][d.id].countStarted=new Date()
            }
            s.makeMonitorObject(d)
        break;
        case'frame':
            d.details={}
            try{
                s.makeMonitorObject(d)
                if(!s.group[d.ke][d.id].buffer){
                  s.group[d.ke][d.id].buffer=[d.frame];
                }else{
                  s.group[d.ke][d.id].buffer.push(d.frame)
                }
                if(d.frame[d.frame.length-2] === 0xFF && d.frame[d.frame.length-1] === 0xD9){
                    if(d.mon.detector_frame_save==="1"){
                       d.base64=s.group[d.ke][d.id].buffer.toString('base64')
                    }
                    if(d.mon.detector_scale_x&&d.mon.detector_scale_x!==''&&d.mon.detector_scale_y&&d.mon.detector_scale_y!==''){
                        d.width=d.mon.detector_scale_x;
                        d.height=d.mon.detector_scale_y;
                    }else{
                        d.width=640
                        d.height=480
                    }
                    s.detectObject(Buffer.concat(s.group[d.ke][d.id].buffer),d)
                    s.group[d.ke][d.id].buffer=null;
                }
            } catch(err){
                    console.error(err)
                }
        break;
    }
})