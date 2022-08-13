// Shinobi (http://shinobi.video) - FFMPEG H.264 over HTTP Test
// How to Use
// 1. Start with `node ffmpegToWeb.js`
// 2. Get the IP address of the computer where you did step 1. Example : 127.0.0.1
// 3. Open VLC and "Open Network Stream".
// 4. Input the following without quotes : `http://127.0.0.1:8001` and start.

var child = require('child_process');
var events = require('events');
var spawn = child.spawn;
var exec = child.exec;
var Emitter = new events.EventEmitter().setMaxListeners(0)
var config = {
    port:8001
}
//ffmpeg
console.log('Starting FFMPEG')
var ffmpeg = spawn('ffmpeg',('-rtsp_transport tcp -i rtsp://131.95.3.162/axis-media/media.3gp -f mpegts -c:v copy -an -').split(' '));
ffmpeg.on('close', function (buffer) {
    console.log('ffmpeg died')
})
//ffmpeg.stderr.on('data', function (buffer) {
//    console.log(buffer.toString())
//});
ffmpeg.stdout.on('data', function (buffer) {
    Emitter.emit('data',buffer)
});
//web app
console.log('Starting Express Web Server on Port '+config.port)
var express = require('express')
var app = express();
var http = require('http')
var httpServer = http.createServer(app);

app.get('/', function (req, res) {
    var contentWriter
    var date = new Date();
    res.writeHead(200, {
        'Date': date.toUTCString(),
        'Connection': 'close',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache',
        'Content-Type': 'video/mp4',
        'Server': 'Shinobi H.264 Test Stream',
    });
    Emitter.on('data',contentWriter=function(buffer){
        res.write(buffer)
    })
    res.on('close', function () {
        Emitter.removeListener('data',contentWriter)
    })
});

httpServer.listen(config.port);