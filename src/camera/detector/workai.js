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
var http = require('http');
var fs = require('fs');
var qs=require('querystring');

var device_SN = null
var DEVICE_UUID_FILEPATH = process.env.DEVICE_UUID_FILEPATH || '/dev/ro_serialno'

function get_device_SN(cb) {
    if(device_SN)
        return cb && cb(null, device_SN)

    fs.readFile(DEVICE_UUID_FILEPATH, 'utf8', function(err, data){
        if(err)
            return cb && cb(err, null)

        var arr = data.split('\n')
        if(arr && arr[0] && arr[0] != '') {
            device_SN = arr[0]
            return cb && cb(null, device_SN)
        }
        else {
            return cb && cb(null, null)
        }
    });
}

function canvas2jpg(d, dir, cb) {
    //var canvas = new Canvas(d.width, d.height);
    //var ctx = canvas.getContext('2d', {alpha: false, pixelFormat: "RGB24"})
    //var filename = dir + 'workai_' + (new Date().getTime()) + '.png'
    //var out = fs.createWriteStream(filename)

    //ctx.imageSmoothingEnabled = true
    //ctx.drawImage(d.image, 0, 0, d.width, d.height)

    //canvas.pngStream().pipe(out)
    //out.on('finish', function () {
    //    console.log("save as " + filename)
    //    return cb && cb(null, filename);
    //})
    //out.on('end', function () {
    //    console.log("canvas2jpg end");
    //})
    //out.on('error', function (err) {
    //    console.log("canvas2jpg error: " + err);
    //})

    var canvas1 = new Canvas(d.width, d.height);
    var ctx = canvas1.getContext('2d')
    ctx.drawImage(d.image, 0, 0, d.width, d.height)

    var filename = dir + 'workai_' + (new Date().getTime()) + '.jpg'
    var out = fs.createWriteStream(filename)
    var stream = canvas1.jpegStream()
    stream.on('end', function () {
        console.log("canvas2jpg end");
        console.log("save as " + filename)
        canvas1 = null
        return cb && cb(null, filename);
    });
    stream.on('error', function (err) {
        console.log("canvas2jpg error: " + err);
    })
    stream.pipe(out);
}
function upload2python(filepath, trackerid, uuid, cb) {
    var arr = filepath.split('\/');
    var filename = arr[arr.length-1];
    var stat = fs.statSync(filepath);

    if(!trackerid || !uuid) {
        return cb && cb("bad args")
    }

    var querystring = "?objid=" + trackerid + "&uuid=" + uuid + "&ts=" + (new Date().getTime());

    var options = {
        host: "workaipython",
        port: "5000" ,
        method: "POST",
        timeout: 10*1000,
        path: "/api/fullimg/" + querystring
    }

    var req = http.request(options, function(res){
        res.on("data", function(chunk){
            console.log("BODY:" + chunk);
        })
    })
    req.on('error', function(e){
        console.log('problem with request:' + e.message);
        console.log(e);
        return cb && cb(e)
    })
    req.on('end', function(e){
        console.log('req.on end:');
        return cb && cb()
    })

    var boundaryKey = Math.random().toString(16);
    var enddata = '\r\n----' + boundaryKey + '--';
    var content = "\r\n----" + boundaryKey + "\r\n" +
                  "Content-Type: application/octet-stream\r\n" +
                  "Content-Disposition: form-data; name=\"" + "file" + "\"; filename=\"" + filename + "\"\r\n" +
                  "Content-Transfer-Encoding: binary\r\n\r\n";
    var contentBinary = new Buffer(content, 'utf-8');

    var contentLength = contentBinary.length + stat.size;

    req.setHeader('Content-Type', 'multipart/form-data; boundary=--' + boundaryKey);
    req.setHeader('Content-Length', contentLength + Buffer.byteLength(enddata));

    req.write(contentBinary);
    var fileStream = fs.createReadStream(filepath, {bufferSize : 4 * 1024});
    fileStream.pipe(req, {end: false});
    fileStream.on('end', function() {
        req.end(enddata);
        return cb && cb()
    });
}
function upload2python_onlyImagePath(filepath, trackerid, uuid, cb) {
    var post_data={imgpath: filepath}
    var content=qs.stringify(post_data);

    var querystring = "?objid=" + trackerid + "&uuid=" + uuid + "&ts=" + (new Date().getTime());

    var options = {
        host: "workaipython",
        port: "5000" ,
        method: "POST",
        path: "/api/fullimg/" + querystring,
        timeout: 10*1000,
        headers:{
            'Content-Type':'application/x-www-form-urlencoded',
            'Content-Length':content.length
        }
    };

    var req = http.request(options, function(res) {
      var _data='';
      res.on('data', function(chunk){
          _data += chunk;
      });
      res.on('end', function(){
          console.log(_data)
          return cb && cb(null, _data)
      });
      res.on('error', function(err){
          return cb && cb(err, _data)
      });
    });

    req.write(content);
    req.end();
}

//isbefore=true 检查发送图片之前的trackerid
function updateTrackerInfo(isBefore, d, sn, respons) {
    var tracker_timeOut = 4000; //2s
    var ts = new Date().getTime()

    //开机第一张图片, 默认初始化个值
    if(!s.group[d.ke][d.id].trackerid) {
        s.group[d.ke][d.id].trackerid = sn + ts
        s.group[d.ke][d.id].lastTimeStatmp = ts
        return
    }

    //发送前, 检查当前图片和上一张有人图片的时间间隔,>4s认为是新的trackerid
    if(isBefore && (ts-s.group[d.ke][d.id].lastTimeStatmp) > tracker_timeOut) {
        s.group[d.ke][d.id].trackerid = sn + ts
        return
    }

    //发送之后, 这张图片有1个人, 更新最后一张图的时间
    if(!isBefore && respons && respons.totalpeople == 1) {
        s.group[d.ke][d.id].lastTimeStatmp = Number(respons.ts)
        return
    }

    //发送之后, 这张图片有2个人, 更新最后一张图的时间, 更新trakcerid
    if(!isBefore && respons && respons.totalpeople > 1) {
        s.group[d.ke][d.id].lastTimeStatmp = Number(respons.ts)
        s.group[d.ke][d.id].trackerid = sn + respons.ts
        return
    }
}

function post2workaipython(d, average) {
    var thrhold = 1000
    if(average < thrhold)
        return;

    var dir = process.env.NODE_ENV || '/data/runtime/cache/';
    var ts = Math.floor(new Date().getTime()/1000)

    get_device_SN(function(snerr, SN){
        if(snerr || !SN)
            return

        updateTrackerInfo(true, d, SN, null);

        canvas2jpg(d, dir, function(err, filepath){
            fs.exists(filepath, function(exists) {
                if(!exists) {
                    return
                }
                setTimeout(function(){
                    var trackerid =  s.group[d.ke][d.id].trackerid
                    //upload2python(filepath, trackerid, SN, function(err) {
                    upload2python_onlyImagePath(filepath, trackerid, SN, function(err, response) {
                        updateTrackerInfo(false, d, SN, JSON.parse(response));
                        if(!err)
                            console.log("send image to python successed")
                        else
                            console.log("send image to python error: " + err)
                    })
                }, 50);
            })
        })
    })
}

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
            d.mon.detector_sensitivity;
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
    //if (average > 30){
        s.cx({f:'trigger',id:d.id,ke:d.ke,details:{plug:config.plug,name:cord.name,reason:'motion',confidence:average}})
        console.log('Has motion, average: ' + average)
        post2workaipython(d, average);
    } else {
        console.log('Sensitivity is ' + parseFloat(cord.sensitivity) + ' average is ' + average);
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
    s.cx({f:'init',plug:config.plug,notice:config.notice,type:config.type});
})
io.on('disconnect',function(d){
    io.connect();
})
io.on('f',function(d){
    switch(d.f){
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
                    s.systemLog('3');
                    if(d.mon.detector_frame_save==="1"){
                       d.base64=s.group[d.ke][d.id].buffer.toString('base64')
                    }
                    s.group[d.ke][d.id].cords=Object.values(d.mon.cords);
                    d.mon.cords=d.mon.cords;
                    d.image = new Canvas.Image;

                    if(d.mon.detector_scale_x===''||d.mon.detector_scale_y===''){
                        s.systemLog('4');
                        s.systemLog('Must set detector image size')
                        return
                    }else{
                        d.image.width=d.mon.detector_scale_x;
                        d.image.height=d.mon.detector_scale_y;
                    }
                    d.image.onload = function() {
                        s.checkAreas(d);
                        time2 = new Date().getTime()
                        console.log(">>> " + (time2-time1))
                    }
                    console.log(s.group[d.ke][d.id].buffer.length)
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
