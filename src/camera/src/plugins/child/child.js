var os = require('os');
var fs = require('fs');
var path = require('path');
var mysql = require('mysql');
var moment = require('moment');
var request = require("request");
var spawn = require('child_process').spawn;
var exec = require('child_process').exec;
var execSync = require('child_process').execSync;
var connectionTester = require('connection-tester');
var config = require('./conf.json');

exec("ps aux | grep -ie ffmpeg | awk '{print $2}' | xargs kill -9");//kill any ffmpeg running
process.on('uncaughtException', function (err) {
    console.error('uncaughtException',err);
});
s={connected:false,child_node:true,platform:os.platform(),group:{}};

//connect to master
io = require('socket.io-client')('ws://'+config.ws);
//spawn conatiner
s.spawns={};
//emulate master sql query
sql={
    query:function(x,y,z){
        io.emit('c',{f:'sql',query:x,values:y});if(typeof z==='function'){z();}
    }
}
//get this nodes cpu usage
s.cpuUsage=function(e){
    switch(s.platform){
        case'darwin':
            e="ps -A -o %cpu | awk '{s+=$1} END {print s}'";
        break;
        case'linux':
            e="grep 'cpu ' /proc/stat | awk '{usage=($2+$4)*100/($2+$4+$5)} END {print usage}'";
        break;
    }
    return execSync(e,{encoding:'utf8'});
}
setInterval(function(){
    io.emit('c',{f:'cpu',cpu:parseFloat(s.cpuUsage())});
},2000);
//interact with server functions
s.cx=function(x){io.emit('c',x)}
//emulate master socket emitter
s.tx=function(x,y){s.cx({f:'s.tx',data:x,to:y})}
//emulate master logger
s.log=function(x,y){console.log(y);s.cx({f:'s.log',data:s.init('clean',x),to:y})}
//emulate master camera function
s.camera=function(x,y){s.cx({f:'camera',mode:x,data:y})}

//load camera controller vars
s.nameToTime=function(x){x=x.split('.')[0].split('T'),x[1]=x[1].replace(/-/g,':');x=x.join(' ');return x;}
s.ratio=function(width,height,ratio){ratio = width / height;return ( Math.abs( ratio - 4 / 3 ) < Math.abs( ratio - 16 / 9 ) ) ? '4:3' : '16:9';}
s.gid=function(x){
    if(!x){x=10};var t = "";var p = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
    for( var i=0; i < x; i++ )
        t += p.charAt(Math.floor(Math.random() * p.length));
    return t;
};
s.moment=function(e,x){if(!e){e=new Date};if(!x){x='YYYY-MM-DDTHH-mm-ss'};return moment(e).utcOffset('-0800').format(x)}
s.kill=function(x,e,p){
    if(e&&s.group[e.ke].mon[e.id].record){
        clearTimeout(s.group[e.ke].mon[e.id].record.capturing);
        if(s.group[e.ke].mon[e.id].record.request&&s.group[e.ke].mon[e.id].record.request.abort){s.group[e.ke].mon[e.id].record.request.abort();delete(s.group[e.ke].mon[e.id].record.request);}
    };
    if(!x||x===1){return};if(!x.stdin){return};p=x.pid;x.stdin.pause();setTimeout(function(){x.kill('SIGTERM');delete(x);setTimeout(function(){exec('kill -9 '+p)},1000)},1000)
}
s.cameraVals=function(e){
    e.t=Object.keys(s.group[e.ke].mon[e.id]);e.a={};
    e.t.forEach(function(n){
       if(s.group[e.ke].mon[e.id][n] instanceof Object){e.a[n]=s.group[e.ke].mon[e.id][n]};
    });
    return e.a;
}
//directories
s.group={};
s.dir={videos:__dirname+'/videos/',frames:__dirname+'/frames/'};
if (!fs.existsSync(s.dir.frames)){
    fs.mkdirSync(s.dir.frames);
}
if (!fs.existsSync(s.dir.videos)){
    fs.mkdirSync(s.dir.videos);
}
////Camera Controller
s.init=function(x,e){
    switch(x){
        case 0://camera
            if(!s.group[e.ke]){s.group[e.ke]={}};
            if(!s.group[e.ke].mon){s.group[e.ke].mon={}}
            if(!s.group[e.ke].mon[e.mid]){s.group[e.ke].mon[e.mid]={}}
            if(!s.group[e.ke].mon[e.mid].watch){s.group[e.ke].mon[e.mid].watch={}};
            if(e.type==='record'){e.record=1}else{e.record=0}
            if(!s.group[e.ke].mon[e.mid].record){s.group[e.ke].mon[e.mid].record={yes:e.record}};
            if(!s.group[e.ke].mon[e.mid].started){s.group[e.ke].mon[e.mid].started={}};
            if(!s.group[e.ke].mon[e.mid].running){s.group[e.ke].mon[e.mid].running={}};
        break;
        case'clean':
            if(e instanceof Object){
                x={keys:Object.keys(e),ar:{}};
                x.keys.forEach(function(v){
                    if(v!=='record'&&v!=='spawn'&&v!=='running'&&(typeof e[v]!=='function')){x.ar[v]=e[v];}
                });
                return x.ar;
            }
        break;
        case'clean':
            x={keys:Object.keys(e),ar:{}};
            x.keys.forEach(function(v){
                if(v!=='record'&&v!=='spawn'&&v!=='running'&&(v!=='time'&&typeof e[v]!=='function')){x.ar[v]=e[v];}
            });
            return x.ar;
        break;
        case'url':
            auth_details='';
            if(e.details.muser&&e.details.muser!==''&&e.details.mpass&&e.details.mpass!=='') {
                auth_details=e.details.muser+':'+e.details.mpass+'@';
            }
            if(e.port==80){e.porty=''}else{e.porty=':'+e.port}
            e.url=e.protocol+'://'+auth_details+e.host+e.porty+e.path;return e.url;
        break;
        case'url_no_path':
            auth_details='';
            if(e.details.muser&&e.details.muser!==''&&e.details.mpass&&e.details.mpass!=='') {
                auth_details=e.details.muser+':'+e.details.mpass+'@';
            }
            if(e.port==80){e.porty=''}else{e.porty=':'+e.port}
            e.url=e.protocol+'://'+auth_details+e.host+e.porty;return e.url;
        break;
    }
    if(typeof e.callback==='function'){setTimeout(function(){e.callback();delete(e.callback);},2000);}
}
s.video=function(x,e){
    if(!e){e={}};
    if(e.mid){e.id=e.mid};
    switch(x){
        case'delete':
            e.dir=s.dir.videos+e.ke+'/'+e.id+'/';
            e.save=[e.id,e.ke,s.nameToTime(e.filename),0];
            sql.query('DELETE FROM Videos WHERE `mid`=? AND `ke`=? AND `time`=? AND `status`=?',e.save)
            s.tx({f:'video_delete',reason:'Camera Error',filename:e.filename+'.'+e.ext,mid:e.id,ke:e.ke,time:s.nameToTime(e.filename),end:moment().format('YYYY-MM-DD HH:mm:ss')},'GRP_'+e.ke);
            if(fs.existsSync(e.dir+e.filename+'.'+e.ext)){
                return fs.unlink(e.dir+e.filename+'.'+e.ext);
            }
        break;
        case'close':
            e.dir=s.dir.videos+e.ke+'/'+e.id+'/';
            console.log(e.dir+e.filename+'.'+e.ext)
            if(fs.existsSync(e.dir+e.filename+'.'+e.ext)){
                e.filesize=fs.statSync(e.dir+e.filename+'.'+e.ext)["size"];
                if((e.filesize/100000).toFixed(2)>0.25){
                    e.save=[e.filesize,e.frames,1,e.id,e.ke,s.nameToTime(e.filename)];
                    sql.query('UPDATE Videos SET `size`=?,`frames`=?,`status`=? WHERE `mid`=? AND `ke`=? AND `time`=?',e.save)
                    fs.readFile(e.dir+e.filename+'.'+e.ext,function (err,data) {
                        s.cx({f:'created_file',mid:e.id,ke:e.ke,created_file:data,filename:e.filename+'.'+e.ext,d:s.init('clean',e)});
                        s.tx({f:'video_build_success',filename:e.filename+'.'+e.ext,mid:e.id,ke:e.ke,time:s.nameToTime(e.filename),size:e.filesize,end:s.moment(new Date,'YYYY-MM-DD HH:mm:ss')},'GRP_'+e.ke);
                    });
                }else{
                    s.video('delete',e);
                    s.log(e,{type:'File Corrupt',msg:{ffmpeg:s.group[e.ke].mon[e.mid].ffmpeg,filesize:(e.filesize/100000).toFixed(2)}})
                }
            }else{
                s.video('delete',e);
                s.log(e,{type:'File Not Exist',msg:'Cannot save non existant file. Something went wrong.',ffmpeg:s.group[e.ke].mon[e.id].ffmpeg})
            }
        break;
    }
}
s.ffmpeg=function(e,x){
    if(!x){x={tmp:''}}
//            if(!e.details.cutoff||e.details.cutoff===''){x.cutoff=15}else{x.cutoff=parseFloat(e.details.cutoff)};if(isNaN(x.cutoff)===true){x.cutoff=15}
//            x.segment=' -f segment -strftime 1 -segment_time '+(60*x.cutoff)+' -segment_format '+e.ext
        if(!e.details.timestamp||e.details.timestamp==1){x.time=' -vf drawtext=fontfile=/usr/share/fonts/truetype/freefont/FreeSans.ttf:text=\'%{localtime}\':x=(w-tw)/2:y=0:fontcolor=white:box=1:boxcolor=0x00000000@1:fontsize=10';}else{x.time=''}
    switch(e.ext){
        case'mp4':
            x.vcodec='libx265';x.acodec='libfaac';
            if(e.details.vcodec&&e.details.vcodec!==''){x.vcodec=e.details.vcodec}
        break;
        case'webm':
            x.acodec='libvorbis',x.vcodec='libvpx';
        break;
    }
    if(e.details.acodec&&e.details.acodec!==''){x.acodec=e.details.acodec}
    if(x.acodec==='none'){x.acodec=''}else{x.acodec=' -acodec '+x.acodec}
    if(x.vcodec!=='none'){x.vcodec=' -vcodec '+x.vcodec}
    if(e.fps&&e.fps!==''){x.framerate=' -r '+e.fps}else{x.framerate=''}
    if(e.details.vf&&e.details.vf!==''){
        if(x.time===''){x.vf=' -vf '}else{x.vf=','}
        x.vf+=e.details.vf;
        x.time+=x.vf;
    }
    if(e.details.svf&&e.details.svf!==''){x.svf=' -vf '+e.details.svf;}else{x.svf='';}
//        if(e.details.svf){'-vf "rotate=45*(PI/180)'}
    switch(e.type){
        case'socket':case'jpeg':case'pipe':
            if(!x.vf||x.vf===','){x.vf=''}
            x.tmp='-loglevel warning -pattern_type glob -f image2pipe'+x.framerate+' -vcodec mjpeg -i -'+x.vcodec+x.time+x.framerate+' -use_wallclock_as_timestamps 1 -q:v 1'+x.vf+' '+e.dir+e.filename+'.'+e.ext;
        break;
        case'mjpeg':
            if(e.mode=='record'){
                x.watch=x.vcodec+x.time+' -r 10 -s '+e.width+'x'+e.height+' -use_wallclock_as_timestamps 1 -q:v 1 '+e.dir+e.filename+'.'+e.ext+''
            }else{
                x.watch='';
            };
            x.tmp='-loglevel warning -reconnect 1 -f mjpeg -i '+e.url+''+x.watch+' -f image2pipe'+x.svf+' -s '+e.ratio+' pipe:1';
        break;
        case'h264':
            if(!x.vf||x.vf===','){x.vf=''}
            if(e.mode=='record'){
                x.watch=x.vcodec+x.framerate+x.acodec+' -movflags frag_keyframe+empty_moov -s '+e.width+'x'+e.height+' -use_wallclock_as_timestamps 1 -q:v 1'+x.vf+' '+e.dir+e.filename+'.'+e.ext
            }else{
                x.watch='';
            };
            x.tmp='-loglevel warning -i '+e.url+' -stimeout 2000'+x.watch+' -f image2pipe'+x.svf+' -s '+e.ratio+' pipe:1';
        break;
        case'local':
            if(e.mode=='record'){
                x.watch=x.vcodec+x.time+x.framerate+x.acodec+' -movflags frag_keyframe+empty_moov -s '+e.width+'x'+e.height+' -use_wallclock_as_timestamps 1 '+e.dir+e.filename+'.'+e.ext
            }else{
                x.watch='';
            };
            x.tmp='-loglevel warning -i '+e.path+''+x.watch+' -f image2pipe'+x.svf+' -s '+e.ratio+' pipe:1';
        break;
    }
    s.group[e.ke].mon[e.mid].ffmpeg=x.tmp;
    return spawn('ffmpeg',x.tmp.split(' '));
}

//child functions
var cn={};
io.on('connect', function(d){
    console.log('connected');
    io.emit('c',{f:'init',socket_key:config.key,u:{name:config.name}})
});
io.on('c',function(d){
    console.log(d.f);
    switch(d.f){
        case'init_success':
            s.connected=true;
            s.other_helpers=d.child_helpers;
        break;
        case'kill':
            s.init(0,d.d);
            s.kill(s.group[d.d.ke].mon[d.d.id].spawn,d.d)
        break;
        case'sync':
            s.init(0,d.sync);
            Object.keys(d.sync).forEach(function(v){
                s.group[d.sync.ke].mon[d.sync.mid][v]=d.sync[v];
            });
        break;
        case'delete_file'://delete video
            d.dir=s.dir.videos+d.ke+'/'+d.mid+'/'+d.file;
            if(fs.existsSync(d.dir)){
                fs.unlink(d.dir);
            }
        break;
        case'close'://close video
            s.video('close',d.d);
        break;
        case'spawn'://start video
            s.init(0,d.d);
            s.group[d.d.ke].mon[d.d.id]=d.mon;
            s.init(0,d.d);
            if(!s.group[d.d.ke].mon_conf){s.group[d.d.ke].mon_conf={}}
            if(!s.group[d.d.ke].mon_conf[d.d.id]){s.group[d.d.ke].mon_conf[d.d.id]=s.init('clean',d.d);}
            if(s.group[d.d.ke].mon[d.d.id].spawn&&s.group[d.d.ke].mon[d.d.id].spawn.stdin){return}
            if(d.d.mode==='record'){
                console.log(s.group[d.d.ke].mon[d.d.id])
                s.group[d.d.ke].mon[d.d.id].record.yes=1;
                d.d.dir=s.dir.videos+d.d.ke+'/';
                if (!fs.existsSync(d.d.dir)){
                    fs.mkdirSync(d.d.dir);
                }
                d.d.dir=s.dir.videos+d.d.ke+'/'+d.d.id+'/';
                if (!fs.existsSync(d.d.dir)){
                    fs.mkdirSync(d.d.dir);
                }
            }else{
                s.group[d.d.ke].mon[d.d.mid].record.yes=0;
            }
            if(d.d.mode==='record'||d.d.type==='mjpeg'||d.d.type==='h264'||d.d.type==='local'){
                s.group[d.d.ke].mon[d.d.id].spawn = s.ffmpeg(d.d);
                s.log(d.d,{type:'FFMPEG Process Starting',msg:{cmd:s.group[d.d.ke].mon[d.d.id].ffmpeg}});
            }
            d.d.frames=0;
            switch(d.d.type){
                case'jpeg':
                  if(!d.d.details.sfps||d.d.details.sfps===''){
                        d.d.details.sfps=parseFloat(d.d.details.sfps);
                        if(isNaN(d.d.details.sfps)){d.d.details.sfps=1}
                    }
                    d.d.captureOne=function(f){
                        s.group[d.d.ke].mon[d.d.id].record.request=request({url:d.d.url,method:'GET',encoding: null,timeout:3000},function(er,data){
                           ++d.d.frames; if(s.group[d.d.ke].mon[d.d.id].spawn&&s.group[d.d.ke].mon[d.d.id].spawn.stdin){
                            if(er){
                                ++d.d.error_count;
                                s.log(d.d,{type:'Snapshot Error',msg:er});
                                return;
                            }
                           if(d.d.mode==='record'&&s.group[d.d.ke].mon[d.d.id].spawn&&s.group[d.d.ke].mon[d.d.id].spawn.stdin){
                               s.group[d.d.ke].mon[d.d.id].spawn.stdin.write(data.body);
                           }
                            if(s.group[d.d.ke].mon[d.d.id].watch&&Object.keys(s.group[d.d.ke].mon[d.d.id].watch).length>0){
                                s.tx({f:'monitor_frame',ke:d.d.ke,id:d.d.id,time:s.moment(),frame:data.body.toString('base64'),frame_format:'b64'},'MON_'+d.d.id);
                            }
                            s.group[d.d.ke].mon[d.d.id].record.capturing=setTimeout(function(){d.d.captureOne()},1000/d.d.details.sfps);
                            clearTimeout(d.d.timeOut),d.d.timeOut=setTimeout(function(){d.d.error_count=0;},3000)
                            }
                        }).on('error', function(err){
//                                                if(s.group[d.d.ke]&&s.group[d.d.ke].mon[d.d.id]&&s.group[d.d.ke].mon[d.d.id].record&&s.group[d.d.ke].mon[d.d.id].record.request){s.group[d.d.ke].mon[d.d.id].record.request.abort();}
                            clearTimeout(s.group[d.d.ke].mon[d.d.id].record.capturing);
                         if(d.d.error_count>4){d.d.fn();return}
                            d.d.captureOne();
                        });
                  }
                  d.d.captureOne()
                break;
                case'mjpeg':case'h264'://case'socket':case'local':
                    if(!s.group[d.d.ke]||!s.group[d.d.ke].mon[d.d.id]){s.init(0,d.d)}
                    if(s.group[d.d.ke].mon[d.d.id].spawn){
                        s.group[d.d.ke].mon[d.d.id].spawn.on('error',function(er){d.d.error({type:'Spawn Error',msg:er})})
                        s.group[d.d.ke].mon[d.d.id].spawn.stdout.on('data',function(de){
                            s.tx({f:'monitor_frame',ke:d.d.ke,id:d.d.id,time:s.moment(),frame:de.toString('base64'),frame_format:'b64'},'MON_'+d.d.id);
                        });
                        s.group[d.d.ke].mon[d.d.id].spawn.stderr.on('data',function(de){
                            de=de.toString();
                            d.d.chk=function(x){return de.indexOf(x)>-1;}
                            switch(true){
//                                                case d.d.chk('av_interleaved_write_frame'):
                                case d.d.chk('Connection timed out'):
                                    setTimeout(function(){s.log(d.d,{type:"Can't Connect",msg:'Retrying...'});d.d.error_fatal();},1000)//restart
                                break;
                                case d.d.chk('No pixel format specified'):
                                    s.log(d.d,{type:"FFMPEG STDERR",msg:{ffmpeg:s.group[d.d.ke].mon[d.d.id].ffmpeg,msg:de}})
                                break;
                                case d.d.chk('RTP: missed'):
                                case d.d.chk('deprecated pixel format used, make sure you did set range correctly'):
                                    return
                                break;
                                case d.d.chk('No such file or directory'):
                                case d.d.chk('Unable to open RTSP for listening'):
                                case d.d.chk('timed out'):
                                case d.d.chk('Invalid data found when processing input'):
                                case d.d.chk('Immediate exit requested'):
                                case d.d.chk('reset by peer'):
                                   if(d.d.frames===0&&x==='record'){s.video('delete',d.d)};
                                break;
                            }
                            s.log(d.d,{type:"FFMPEG STDERR",msg:de})
                        });
                    }
                break;
            }
        break;
        case'video':
            s.video(d.d[0],d.d[1]);
        break;
    }
});
io.on('disconnect',function(d){
    s.connected=false;
});