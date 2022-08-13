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
var Cluster = require('./libs/clusterPoints.js');
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
s.checkRegion=function(d,cord){
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
    s.group[d.ke][d.id].canvasContext[cord.name].drawImage(d.image, 0, 0, d.width, d.height);
    var blenderCanvas = s.group[d.ke][d.id].canvas[cord.name];
    var blenderCanvasContext = s.group[d.ke][d.id].canvasContext[cord.name];
    s.group[d.ke][d.id].frameSelected[s.group[d.ke][d.id].frameNumber] = blenderCanvasContext.getImageData(0, 0, blenderCanvas.width, blenderCanvas.height);
    s.group[d.ke][d.id].frameNumber = 0 == s.group[d.ke][d.id].frameNumber ? 1 : 0;
    s.group[d.ke][d.id].lastRegionImageData = blenderCanvasContext.getImageData(0, 0, blenderCanvas.width, blenderCanvas.height);
    if(!s.group[d.ke][d.id].lastRegionImageData){return}
    var foundPixels = [];
    var average = 0;
    var currentImageLength = s.group[d.ke][d.id].lastRegionImageData.data.length * 0.25;
    for (b = 0; b < currentImageLength;){
        var pos = b * 4
        s.group[d.ke][d.id].lastRegionImageData.data[pos] = .5 * (255 - s.group[d.ke][d.id].lastRegionImageData.data[pos]) + .5 * s.group[d.ke][d.id].frameSelected[s.group[d.ke][d.id].frameNumber].data[pos];
        s.group[d.ke][d.id].lastRegionImageData.data[pos + 1] = .5 * (255 - s.group[d.ke][d.id].lastRegionImageData.data[pos + 1]) + .5 * s.group[d.ke][d.id].frameSelected[s.group[d.ke][d.id].frameNumber].data[pos + 1];
        s.group[d.ke][d.id].lastRegionImageData.data[pos + 2] = .5 * (255 - s.group[d.ke][d.id].lastRegionImageData.data[pos + 2]) + .5 * s.group[d.ke][d.id].frameSelected[s.group[d.ke][d.id].frameNumber].data[pos + 2];
        s.group[d.ke][d.id].lastRegionImageData.data[pos + 3] = 255;
        var score = (s.group[d.ke][d.id].lastRegionImageData.data[pos] + s.group[d.ke][d.id].lastRegionImageData.data[pos + 1] + s.group[d.ke][d.id].lastRegionImageData.data[pos + 2]) / 3;
        if(score>170){
            var x = (pos / 4) % d.width;
            var y = Math.floor((pos / 4) / d.width);
            foundPixels.push([x,y])
        }
        
        average += (s.group[d.ke][d.id].lastRegionImageData.data[b * 4] + s.group[d.ke][d.id].lastRegionImageData.data[b * 4 + 1] + s.group[d.ke][d.id].lastRegionImageData.data[b * 4 + 2]);
        
        b += 4;
    }
//    console.log(foundPixels)
    var matrices
    if(d.mon.detector_region_of_interest==='1'&&foundPixels.length>0){
        var groupedPoints = Object.assign({},Cluster);
        groupedPoints.iterations(25);
        groupedPoints.data(foundPixels);
        var groupedPoints = groupedPoints.clusters()
        var matrices=[]
        var mostHeight = 0;
        var mostWidth = 0;
        var mostWithMotion = null;
        groupedPoints.forEach(function(v,n){
            var matrix = {
                topLeft:[d.width,d.height],
                topRight:[0,d.height],
                bottomRight:[0,0],
                bottomLeft:[d.width,0],
            }
            v.points.forEach(function(b){
                var x = b[0]
                var y = b[1]
                if(x<matrix.topLeft[0])matrix.topLeft[0]=x;
                if(y<matrix.topLeft[1])matrix.topLeft[1]=y;
                //Top Right point
                if(x>matrix.topRight[0])matrix.topRight[0]=x;
                if(y<matrix.topRight[1])matrix.topRight[1]=y;
                //Bottom Right point
                if(x>matrix.bottomRight[0])matrix.bottomRight[0]=x;
                if(y>matrix.bottomRight[1])matrix.bottomRight[1]=y;
                //Bottom Left point
                if(x<matrix.bottomLeft[0])matrix.bottomLeft[0]=x;
                if(y>matrix.bottomLeft[1])matrix.bottomLeft[1]=y;
            })
            matrix.x = matrix.topLeft[0];
            matrix.y = matrix.topLeft[1];
            matrix.width = matrix.topRight[0] - matrix.topLeft[0]
            matrix.height = matrix.bottomLeft[1] - matrix.topLeft[1]

            if(matrix.width>mostWidth&&matrix.height>mostHeight){
                mostWidth = matrix.width;
                mostHeight = matrix.height;
                mostWithMotion = matrix;
            }

            matrices.push(matrix)
        })
    }
    average = (average / (currentImageLength));
    if (average > parseFloat(cord.sensitivity)){
        s.cx({f:'trigger',id:d.id,ke:d.ke,details:{plug:config.plug,name:cord.name,reason:'motion',confidence:average,matrices:matrices}})
    }
    s.group[d.ke][d.id].canvasContext[cord.name].clearRect(0, 0, d.width, d.height);
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
        s.checkRegion(d,s.group[d.ke][d.id].cords[b])
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
                s.group[d.ke][d.id].lastRegionImageData=undefined
                s.group[d.ke][d.id].frameNumber=0
                s.group[d.ke][d.id].frameSelected=[]
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
                        lastRegionImageData:undefined,
                        frameNumber:0,
                        frameSelected:[],
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