//
// Shinobi - Motion Plugin
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
var fs = require('fs');
var moment = require('moment');
var Canvas = require('canvas');
var config=require('./conf.json');
if(process.argv[2]&&process.argv[3]){
    config.host=process.argv[2]
    config.port=process.argv[3]
    config.key=process.argv[4]
}
if(config.systemLog===undefined){config.systemLog=true}
s={
    group:{},
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
    if (average > parseFloat(cord.sensitivity)){
        s.cx({f:'trigger',id:d.id,ke:d.ke,details:{plug:config.plug,name:cord.name,reason:'motion',confidence:average}})

    }
    s.group[d.ke][d.id].canvasContext[cord.name].clearRect(0, 0, d.width, d.height);
    s.group[d.ke][d.id].blendRegionContext[cord.name].clearRect(0, 0, d.width, d.height);
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
                    if((typeof d.mon.cords ==='string')&&d.mon.cords.trim()===''){
                        d.mon.cords=[]
                    }else{
                        try{
                            d.mon.cords=JSON.parse(d.mon.cords)
                        }catch(err){
                        }
                    }
                    if(d.mon.detector_frame_save==="1"){
                       d.base64=s.group[d.ke][d.id].buffer.toString('base64')
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
                    d.image.onload = function() { 
                        s.checkAreas(d);
                    }
                    d.image.src = s.group[d.ke][d.id].buffer;
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