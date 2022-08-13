window.chartColors = {
    red: 'rgb(255, 99, 132)',
    orange: 'rgb(255, 159, 64)',
    yellow: 'rgb(255, 205, 86)',
    green: 'rgb(75, 192, 192)',
    blue: 'rgb(54, 162, 235)',
    purple: 'rgb(153, 102, 255)',
    grey: 'rgb(201, 203, 207)'
};
$user.details=JSON.parse($user.details)
$.ccio={fr:$('#files_recent'),mon:{}};
if(!$user.details.lang||$user.details.lang==''){
    $user.details.lang="<%-config.language%>"
}
switch($user.details.lang){
    case'ar'://Arabic
    case'bn'://Bengali
        $('body').addClass('right-to-left')
        $('.mdl-menu__item').each(function(n,v){
            v=$(v).find('i')
            v.appendTo(v.parent())
        })
    break;
}

    $.ccio.log=function(x,y,z){
        if($.ccio.op().browserLog==="1"){
            if(!y){y=''};if(!z){z=''};
            console.log(x,y,z)
        }
    }
    $.ccio.gid=function(x){
        if(!x){x=10};var t = "";var p = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
        for( var i=0; i < x; i++ )
            t += p.charAt(Math.floor(Math.random() * p.length));
        return t;
    };
    $.ccio.init=function(x,d,user,k){
        if(!k){k={}};k.tmp='';
        if(d&&d.user){
            user=d.user
        }
        if(!user){
            user=$user
        }
        switch(x){
            case'cleanMon':
                var acceptedFields = [
                    'mid',
                    'ke',
                    'name',
                    'shto',
                    'shfr',
                    'details',
                    'type',
                    'ext',
                    'protocol',
                    'host',
                    'path',
                    'port',
                    'fps',
                    'mode',
                    'width',
                    'height'
                ]
                var row = {};
                $.each(d,function(m,b){
                    if(acceptedFields.indexOf(m)>-1){
                        row[m]=b;
                    }
                })
                return row
            break;
            case'cleanMons':
                if(d==='object'){
                    var arr={}
                }else{
                    var arr=[]
                }
                $.each($.ccio.mon,function(n,v){
                    var row = $.ccio.init('cleanMon',v)
                    if(d==='object'){
                        arr[n]=row
                    }else{
                        arr.push(row)
                    }
                })
                return arr;
            break;
            case'location':
                var url
                if(d&&d.info&&d.info.URL){
                    url=d.info.URL
                    if(url.charAt(url.length-1)!=='/'){
                        url=url+'/'
                    }
                }else{
                    url='/'
                }
                return url
            break;
//            case'streamWindow':
//                return $('.monitor_item[mid="'+d.id+'"][ke="'+d.ke+'"][auth="'+user.auth_token+'"]')
//            break;
            case'streamMotionDetectRestart':
                $.ccio.init('streamMotionDetectOff',d,user)
                $.ccio.init('streamMotionDetectOn',d,user)
            break;
            case'streamMotionDetectOff':
                d.mon.motionDetectionRunning = false
                $('.monitor_item[mid="'+d.mid+'"][ke="'+d.ke+'"][auth="'+user.auth_token+'"] .zoomGlass').remove()
                clearInterval(d.mon.motionDetector)
            break;
            case'streamMotionDetectOn':
                switch(JSON.parse(d.mon.details).stream_type){
                    case'hls':case'flv':case'mp4':
                        //pass
                    break;
                    default:
                        return $.ccio.init('note',{title:'Client-side Detector',text:'Could not be started. Only <b>FLV</b> and <b>HLS</b> can use this feature.',type:'error'});
                    break;

                }
                d.mon.motionDetectorNextDraw = true
                d.mon.motionDetectionRunning = true
                $.ccio.snapshot(d,function(url){
                    $('#temp').html('<img>')
                    var img=$('#temp img')[0]
                    img.onload=function(){
                        var frameNumber = 0,
                            mainWindow = $('.monitor_item[mid="'+d.mid+'"][ke="'+d.ke+'"][auth="'+user.auth_token+'"]'),
                            blenderCanvas = mainWindow.find(".blenderCanvas"),
                            motionVision = mainWindow.find(".motionVision"),
                            streamElement = mainWindow.find('.stream-element'),
                            streamElementTag = streamElement[0],
                            lastURL = null,
                            currentImage = null,
                            f = [],
                            drawMatrices = {
                                e:mainWindow,
                                monitorDetails:JSON.parse(d.mon.details),
                                stream:streamElement,
                                streamObjects:mainWindow.find('.stream-objects'),
                                details:{
                                    name:'clientSideDetection',
                                }
                            };
                        widthRatio = streamElement.width() / img.width
                        heightRatio = streamElement.height() / img.height
                        drawMatrices.monitorDetails.detector_scale_x = img.width;
                        drawMatrices.monitorDetails.detector_scale_y = img.height;
                        function checkForMotion() {
                            blenderCanvas.width = img.width;
                            blenderCanvas.height = img.height;
                            blenderCanvasContext.drawImage(streamElementTag, 0, 0);
                            f[frameNumber] = blenderCanvasContext.getImageData(0, 0, blenderCanvas.width, blenderCanvas.height);
                            frameNumber = 0 == frameNumber ? 1 : 0;
                            currentImage = blenderCanvasContext.getImageData(0, 0, blenderCanvas.width, blenderCanvas.height);
                            foundPixels = [];
                            for (var currentImageLength = currentImage.data.length * 0.25, b = 0; b < currentImageLength;){
                                var pos = b * 4
                                currentImage.data[pos] = .5 * (255 - currentImage.data[pos]) + .5 * f[frameNumber].data[pos];
                                currentImage.data[pos + 1] = .5 * (255 - currentImage.data[pos + 1]) + .5 * f[frameNumber].data[pos + 1];
                                currentImage.data[pos + 2] = .5 * (255 - currentImage.data[pos + 2]) + .5 * f[frameNumber].data[pos + 2];
                                currentImage.data[pos + 3] = 255;
                                var score = (currentImage.data[pos] + currentImage.data[pos + 1] + currentImage.data[pos + 2]) / 3;
                                if(score>170){
                                    var x = (pos / 4) % img.width;
                                    var y = Math.floor((pos / 4) / img.width);
                                    foundPixels.push([x,y])
                                }
                                b += 4;
                            }
                            var groupedPoints = Object.assign({},Cluster);
                            groupedPoints.iterations(25);
                            groupedPoints.data(foundPixels);
                            var groupedPoints = groupedPoints.clusters()
                            drawMatrices.details.matrices=[]
                            var mostHeight = 0;
                            var mostWidth = 0;
                            var mostWithMotion = null;
                            groupedPoints.forEach(function(v,n){
                                var matrix = {
                                    topLeft:[img.width,img.height],
                                    topRight:[0,img.height],
                                    bottomRight:[0,0],
                                    bottomLeft:[img.width,0],
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

                                drawMatrices.details.matrices.push(matrix)
                            })
                            $.ccio.magnifyStream({
                                p:mainWindow,
                                useCanvas:true,
                                zoomAmount:1,
                                auto:true,
                                animate:true,
                                pageX:((mostWithMotion.width / 2) + mostWithMotion.x) * widthRatio,
                                pageY:((mostWithMotion.height / 2) + mostWithMotion.y) * heightRatio
                            })
                            $.ccio.init('drawMatrices',drawMatrices)
                            if(d.mon.motionDetectorNextDraw===true){
                                clearTimeout(d.mon.motionDetectorNextDrawTimeout)
                                d.mon.motionDetectorNextDrawTimeout=setTimeout(function(){
                                    d.mon.motionDetectorNextDraw = true;
                                },1000)
                                d.mon.motionDetectorNextDraw = false;
//                                console.log({
//                                    p:mainWindow,
//                                    pageX:((matrix.width / 2) + matrix.x) * widthRatio,
//                                    pageY:((matrix.height / 2) + matrix.y) * heightRatio
//                                })
                            }
                            return drawMatrices.details.matrices;
                        }
                        if(blenderCanvas.length === 0){
                            mainWindow.append('<div class="zoomGlass"><canvas class="blenderCanvas"></canvas></div>')
                            blenderCanvas = mainWindow.find(".blenderCanvas")
                        }
                        blenderCanvas = blenderCanvas[0];
                        var blenderCanvasContext = blenderCanvas.getContext("2d");
                        clearInterval(d.mon.motionDetector)
                        d.mon.motionDetector = setInterval(checkForMotion,2000)
                    }
                    img.src=url
                })
            break;
            case'streamURL':
                var streamURL
                switch(JSON.parse(d.details).stream_type){
                    case'jpeg':
                        streamURL=$.ccio.init('location',user)+user.auth_token+'/jpeg/'+d.ke+'/'+d.mid+'/s.jpg'
                    break;
                    case'mjpeg':
                        streamURL=$.ccio.init('location',user)+user.auth_token+'/mjpeg/'+d.ke+'/'+d.mid
                    break;
                    case'hls':
                        streamURL=$.ccio.init('location',user)+user.auth_token+'/hls/'+d.ke+'/'+d.mid+'/s.m3u8'
                    break;
                    case'flv':
                        streamURL=$.ccio.init('location',user)+user.auth_token+'/flv/'+d.ke+'/'+d.mid+'/s.flv'
                    break;
                    case'mp4':
                        streamURL=$.ccio.init('location',user)+user.auth_token+'/mp4/'+d.ke+'/'+d.mid+'/s.mp4'
                    break;
                    case'b64':
                        streamURL='Websocket'
                    break;
                }
                return streamURL
            break;
            case'humanReadMode':
                switch(d){
                    case'idle':
                        k.mode='<%-cleanLang(lang['Idle'])%>'
                    break;
                    case'stop':
                        k.mode='<%-cleanLang(lang['Disabled'])%>'
                    break;
                    case'record':
                        k.mode='<%-cleanLang(lang['Record'])%>'
                    break;
                    case'start':
                        k.mode='<%-cleanLang(lang['Watch Only'])%>'
                    break;
                }
                return k.mode
            break;
            case'monitorInfo':
                d.e=$('.glM'+d.mon.mid+user.auth_token);
                if(JSON.parse(d.mon.details).vcodec!=='copy'&&d.mon.mode=='record'){
                    d.e.find('.monitor_not_record_copy').show()
                }else{
                    d.e.find('.monitor_not_record_copy').hide()
                }
                d.e.find('.monitor_name').text(d.mon.name)
                d.e.find('.monitor_mid').text(d.mon.mid)
                d.e.find('.monitor_ext').text(d.mon.ext);
                d.mode=$.ccio.init('humanReadMode',d.mon.mode,user)
                d.e.find('.monitor_mode').text(d.mode)
                d.e.attr('mode',d.mode)
                d.e.find('.lamp').attr('title',d.mode)
            break;
            case'fullscreen':
                if (d.requestFullscreen) {
                  d.requestFullscreen();
                } else if (d.mozRequestFullScreen) {
                  d.mozRequestFullScreen();
                } else if (d.webkitRequestFullscreen) {
                  d.webkitRequestFullscreen(Element.ALLOW_KEYBOARD_INPUT);
                }
            break;
            case'drawPoints':
                d.height=d.stream.height()
                d.width=d.stream.width()
                if(d.monitorDetails.detector_scale_x===''){d.monitorDetails.detector_scale_x=320}
                if(d.monitorDetails.detector_scale_y===''){d.monitorDetails.detector_scale_y=240}

                d.widthRatio=d.width/d.monitorDetails.detector_scale_x
                d.heightRatio=d.height/d.monitorDetails.detector_scale_y

                d.streamObjects.find('.stream-detected-point[name="'+d.details.name+'"]').remove()
                d.tmp=''
                $.each(d.details.points,function(n,v){
                    d.tmp+='<div class="stream-detected-point" name="'+d.details.name+'" style="height:'+1+'px;width:'+1+'px;top:'+(d.heightRatio*v.x)+'px;left:'+(d.widthRatio*v.y)+'px;">'
                    if(v.tag){d.tmp+='<span class="tag">'+v.tag+'</span>'}
                    d.tmp+='</div>'
                })
                d.streamObjects.append(d.tmp)
            break;
            case'drawMatrices':
                d.height=d.stream.height()
                d.width=d.stream.width()
                if(d.monitorDetails.detector_scale_x===''){d.monitorDetails.detector_scale_x=320}
                if(d.monitorDetails.detector_scale_y===''){d.monitorDetails.detector_scale_y=240}

                d.widthRatio=d.width/d.monitorDetails.detector_scale_x
                d.heightRatio=d.height/d.monitorDetails.detector_scale_y

                d.streamObjects.find('.stream-detected-object[name="'+d.details.name+'"]').remove()
                d.tmp=''
                $.each(d.details.matrices,function(n,v){
                    d.tmp+='<div class="stream-detected-object" name="'+d.details.name+'" style="height:'+(d.heightRatio*v.height)+'px;width:'+(d.widthRatio*v.width)+'px;top:'+(d.heightRatio*v.y)+'px;left:'+(d.widthRatio*v.x)+'px;">'
                    if(v.tag){d.tmp+='<span class="tag">'+v.tag+'</span>'}
                    d.tmp+='</div>'
                })
                d.streamObjects.append(d.tmp)
            break;
            case'clearTimers':
                if(!d.mid){d.mid=d.id}
                if($.ccio.mon[d.ke+d.mid+user.auth_token]){
                    clearTimeout($.ccio.mon[d.ke+d.mid+user.auth_token]._signal);
                    clearInterval($.ccio.mon[d.ke+d.mid+user.auth_token].hlsGarbageCollectorTimer)
                    clearTimeout($.ccio.mon[d.ke+d.mid+user.auth_token].jpegInterval);
                    clearInterval($.ccio.mon[d.ke+d.mid+user.auth_token].signal);
                    clearInterval($.ccio.mon[d.ke+d.mid+user.auth_token].m3uCheck);
                }
            break;
            case'note':
                k.o=$.ccio.op().switches
                if(k.o&&k.o.notifyHide!==1){
                    new PNotify(d)
                }
            break;
            case'montage':
                k.dimensions=$.ccio.op().montage
                k.monitors=$('.monitor_item');
                $.each([1,2,3,4,5,'5ths',6,7,8,9,10,11,12],function(n,v){
                    k.monitors.removeClass('col-md-'+v)
                })
                if(!$('#monitors_live').hasClass('montage')){
                    k.dimensions='2'
                }else{
                    if(!k.dimensions){
                        k.dimensions='3'
                    }
                }
                switch((k.dimensions).toString()){
                    case'1':
                        k.class='12'
                    break;
                    case'2':
                        k.class='6'
                    break;
                    case'4':
                        k.class='3'
                    break;
                    case'5':
                        k.class='5ths'
                    break;
                    case'6':
                        k.class='2'
                    break;
                   default://3
                        k.class='4'
                    break;
                }
                k.class='col-md-'+k.class;
                k.monitors.addClass(k.class)
            break;
            case'monitorOrder':
                k.order = user.details.monitorOrder;
                if(!k.order){
                    k.order=[];
                    $('#monitors_list .link-monitors-list[auth="'+user.auth_token+'"][ke="'+user.ke+'"] .monitor_block').each(function(n,v){
                        v=$(v).attr('mid')
                        if(v){
                            k.order.push(v)
                        }
                    })
                }
                k.switches=$.ccio.op().switches
                k.lists = ['#monitors_list .link-monitors-list[auth="'+user.auth_token+'"][ke="'+user.ke+'"]']
                if(k.switches&&k.switches.monitorOrder===1){
                    k.lists.push('#monitors_live')
                }
                if(d&&d.no&&d.no instanceof Array){
                    k.arr=[]
                    $.each(k.lists,function(n,v){
                        if(d.no.indexOf(v)===-1){
                            k.arr.push(v)
                        }
                    })
                    k.lists=k.arr;
                }
                $.each(k.lists,function(n,v){
                    v = $(v);
                    for(var i = 0, len = k.order.length; i < len; ++i) {
                        v.children('[mid=' + k.order[i] + '][auth="'+user.auth_token+'"]').appendTo(v);
                    }
                    v.find('video').each(function(m,b){
                        b=$(b).parents('.monitor_item')
                        $.ccio.cx({f:'monitor',ff:'watch_on',id:b.attr('mid')},user);
                    })
                })
                return k.order
            break;
            case'monGroup':
                $.ccio.mon_groups={};
                $.each($.ccio.mon,function(n,v,x){
                    if(typeof v.details==='string'){
                        k.d=JSON.parse(v.details)
                    }else{
                        k.d=v.details
                    }
                    try{
                        k.groups=JSON.parse(k.d.groups)
                        $.each(k.groups,function(m,b){
                            if(!$.ccio.mon_groups[b])$.ccio.mon_groups[b]={}
                            $.ccio.mon_groups[b][v.mid]=v;
                        })
                    }catch(er){
                           
                    }
                })
                return $.ccio.mon_groups;
            break;
            case'jpegModeStop':
                clearTimeout($.ccio.mon[d.ke+d.mid+user.auth_token].jpegInterval);
                delete($.ccio.mon[d.ke+d.mid+user.auth_token].jpegInterval);
                $('#monitor_live_'+d.mid+user.auth_token+' .stream-element').unbind('load')
            break;
            case'jpegMode':
                if(d.watch===1){
                    k=JSON.parse(d.details);
                    k.jpegInterval=parseFloat(k.jpegInterval);
                    if(!k.jpegInterval||k.jpegInterval===''||isNaN(k.jpegInterval)){k.jpegInterval=1}
                    $.ccio.tm('stream-element',$.ccio.mon[d.ke+d.mid+user.auth_token]);
                    k.e=$('#monitor_live_'+d.mid+user.auth_token+' .stream-element');
                    $.ccio.init('jpegModeStop',d,user);
                    k.run=function(){
                        k.e.attr('src',user.auth_token+'/jpeg/'+d.ke+'/'+d.mid+'/s.jpg?time='+(new Date()).getTime())
                    }
                    k.e.load(function(){
                        $.ccio.mon[d.ke+d.mid+user.auth_token].jpegInterval=setTimeout(k.run,1000/k.jpegInterval);
                    }).error(function(){
                        $.ccio.mon[d.ke+d.mid+user.auth_token].jpegInterval=setTimeout(k.run,1000/k.jpegInterval);
                    })
                    k.run()
                };
            break;
            case'jpegModeAll':
                $.each($.ccio.mon,function(n,v){
                    $.ccio.init('jpegMode',v,user)
                });
            break;
            case'dragWindows':
                k.e=$("#monitors_live");
                if(k.e.disableSelection){k.e.disableSelection()};
                k.e.sortable({
                  handle: ".mdl-card__supporting-text",
                  placeholder: "ui-state-highlight col-md-6"
                });
            break;
            case'getLocation':
                var l = document.createElement("a");
                l.href = d;
                return l;
            break;
            case 'ls'://livestamp all
                g={e:jQuery('.livestamp')};
                g.e.each(function(){g.v=jQuery(this),g.t=g.v.attr('title');if(!g.t){return};g.v.toggleClass('livestamp livestamped').attr('title',$.ccio.init('t',g.t,user)).livestamp(g.t);})
                return g.e
            break;
            case't'://format time
                if(!d){d=new Date();}
                return moment(d).format('YYYY-MM-DD HH:mm:ss')
            break;
            case'th'://format time hy
                if(!d){d=new Date();}
                return moment(d).format('YYYY-MM-DDTHH:mm:ss')
            break;
            case'tf'://time to filename
                if(!d){d=new Date();}
                return moment(d).format('YYYY-MM-DDTHH-mm-ss')
            break;
            case'fn'://row to filename
                return $.ccio.init('tf',d.time,user)+'.'+d.ext
            break;
            case'filters':
                k.tmp='<option value="" selected><%-cleanLang(lang['Add New'])%></option>';
                $.each(user.details.filters,function(n,v){
                    k.tmp+='<option value="'+v.id+'">'+v.name+'</option>'
                });
                $('#saved_filters').html(k.tmp)
            break;
            case'id':
                $('.usermail').html(d.mail)
                try{k.d=JSON.parse(d.details);}catch(er){k.d=d.details;}
                try{user.mon_groups=JSON.parse(k.d.mon_groups);}catch(er){}
                if(!user.mon_groups)user.mon_groups={};
                $.sM.reDrawMonGroups()
                $.each(user,function(n,v){$.sM.e.find('[name="'+n+'"]').val(v).change()})
                $.each(k.d,function(n,v){$.sM.e.find('[detail="'+n+'"]').val(v).change()})
                $.gR.drawList();
                $.ccio.pm('link-set',k.d.links,null,user)
            break;
            case'jsontoblock'://draw json as block
                if(d instanceof Object){
                    $.each(d,function(n,v){
                        k.tmp+='<div>';
                        k.tmp+='<b>'+n+'</b> : '+$.ccio.init('jsontoblock',v,user);
                        k.tmp+='</div>';
                    })
                }else{
                    k.tmp+='<span>';
                    k.tmp+=d;
                    k.tmp+='</span>';
                }
            break;
            case'url':
                if(d.port==80){d.porty=''}else{d.porty=':'+d.port}
                d.url=d.protocol+'://'+d.host+d.porty;return d.url;
            break;
            case'data-video':
                if(!d){
                    $('[data-mid]').each(function(n,v){
                        v=$(v);v.attr('mid',v.attr('data-mid'))
                    });
                    $('[data-ke]').each(function(n,v){
                        v=$(v);v.attr('ke',v.attr('data-ke'))
                    });
                    $('[data-file]').each(function(n,v){
                        v=$(v);v.attr('file',v.attr('data-file'))
                    });
                    $('[data-status]').each(function(n,v){
                        v=$(v);v.attr('status',v.attr('data-status'))
                    });
                    $('[data-auth]').each(function(n,v){
                        v=$(v);v.attr('auth',v.attr('data-auth'))
                    });
                }else{
                    $('[data-ke="'+d.ke+'"][data-mid="'+d.mid+'"][data-file="'+d.filename+'"][auth="'+user.auth_token+'"]').attr('mid',d.mid).attr('ke',d.ke).attr('status',d.status).attr('file',d.filename).attr('auth',user.auth_token);
                }
            break;
            case'signal':
                d.mon=$.ccio.mon[d.ke+d.id+user.auth_token];d.e=$('#monitor_live_'+d.id+user.auth_token+' .signal').addClass('btn-success').removeClass('btn-danger');d.signal=parseFloat(JSON.parse(d.mon.details).signal_check);
                if(!d.signal||d.signal==NaN){d.signal=10;};d.signal=d.signal*1000*60;
                clearTimeout($.ccio.mon[d.ke+d.id+user.auth_token]._signal);$.ccio.mon[d.ke+d.id+user.auth_token]._signal=setTimeout(function(){d.e.addClass('btn-danger').removeClass('btn-success');},d.signal)
            break;
            case'signal-check':
                try{
                d.mon=$.ccio.mon[d.ke+d.id+user.auth_token];d.p=$('#monitor_live_'+d.id+user.auth_token);
                    try{d.d=JSON.parse(d.mon.details)}catch(er){d.d=d.mon.details;}
                d.check={c:0};
                d.fn=function(){
                    if(!d.speed){d.speed=1000}
                    switch(d.d.stream_type){
                        case'b64':
                            d.p.resize()
                        break;
                        case'hls':case'flv':case'mp4':
                            if(d.p.find('video')[0].paused){
                                if(d.d.signal_check_log==1){
                                    d.log={type:'Stream Check',msg:'<%-cleanLang(lang.clientStreamFailedattemptingReconnect)%>'}
                                    $.ccio.tm(4,d,'#logs,.monitor_item[mid="'+d.id+'"][ke="'+d.ke+'"][auth="'+user.auth_token+'"] .logs')
                                }
                                $.ccio.cx({f:'monitor',ff:'watch_on',id:d.id},user);
                            }else{
                                if(d.d.signal_check_log==1){
                                    d.log={type:'Stream Check',msg:'Success'}
                                    $.ccio.tm(4,d,'#logs,.monitor_item[mid="'+d.id+'"][ke="'+d.ke+'"][auth="'+user.auth_token+'"] .logs')
                                }
                                $.ccio.init('signal',d,user);
                            }
                        break;
                        default:
                            if($.ccio.op().jpeg_on===true){return}
                            $.ccio.snapshot(d,function(url){
                                d.check.f=url;
                                setTimeout(function(){
                                    $.ccio.snapshot(d,function(url){
                                        if(d.check.f===url){
                                            if(d.check.c<3){
                                                ++d.check.c;
                                                setTimeout(function(){
                                                    d.fn();
                                                },d.speed)
                                            }else{
                                                if(d.d.signal_check_log==1){
                                                    d.log={type:'Stream Check',msg:'Client side ctream check failed, attempting reconnect.'}
                                                    $.ccio.tm(4,d,'#logs,.monitor_item[mid="'+d.id+'"][ke="'+d.ke+'"][auth="'+user.auth_token+'"] .logs')
                                                }
                                                delete(d.check)
                                                $.ccio.cx({f:'monitor',ff:'watch_on',id:d.id},user);
                                            }
                                        }else{
                                            if(d.d.signal_check_log==1){
                                                d.log={type:'Stream Check',msg:'Success'}
                                                $.ccio.tm(4,d,'#logs,.monitor_item[mid="'+d.id+'"][ke="'+d.ke+'"][auth="'+user.auth_token+'"] .logs')
                                            }
                                            delete(d.check)
                                            $.ccio.init('signal',d,user);
                                        }
                                    });
                                },d.speed)
                            });
                        break;
                    }
                }
                d.fn();
                }catch(er){
                    er=er.stack;
                    d.in=function(x){return er.indexOf(x)>-1}
                    switch(true){
                        case d.in("The HTMLImageElement provided is in the 'broken' state."):
                            delete(d.check)
                            $.ccio.cx({f:'monitor',ff:'watch_on',id:d.id},user);
                        break;
                        default:
                            $.ccio.log('signal-check',er)
                        break;
                    }
                    clearInterval($.ccio.mon[d.ke+d.id+user.auth_token].signal);delete($.ccio.mon[d.ke+d.id+user.auth_token].signal);
                }
            break;
        }
        return k.tmp;
    }
    $.ccio.snapshot=function(e,cb){
        var image_data,url;
        e.details=JSON.parse(e.mon.details);
        if($.ccio.op().jpeg_on!==true){
            var extend=function(image_data,width,height){
                var len = image_data.length
                var arraybuffer = new Uint8Array( len );
                for (var i = 0; i < len; i++)        {
                    arraybuffer[i] = image_data.charCodeAt(i);
                }
                try {
                    var blob = new Blob([arraybuffer], {type: 'application/octet-stream'});
                } catch (e) {
                    var bb = new (window.WebKitBlobBuilder || window.MozBlobBuilder);
                    bb.append(arraybuffer);
                    var blob = bb.getBlob('application/octet-stream');
                }
                url = (window.URL || window.webkitURL).createObjectURL(blob);
                finish(url,image_data,width,height);
                try{
                    setTimeout(function(){
                        URL.revokeObjectURL(url)
                    },10000)
                }catch(er){}
            }
            var finish = function(url,image_data,width,height){
                cb(url,image_data,width,height);
            }
            switch(JSON.parse(e.mon.details).stream_type){
                case'hls':case'flv':case'mp4':
                    $.ccio.snapshotVideo($('[mid='+e.mon.mid+'].monitor_item video')[0],function(base64,video_data,width,height){
                        extend(video_data,width,height)
                    })
                break;
                case'mjpeg':
                    $('#temp').html('<canvas></canvas>')
                    var c = $('#temp canvas')[0];
                    var img = $('img',$('[mid='+e.mon.mid+'].monitor_item .stream-element').contents())[0];
                    c.width = img.width;
                    c.height = img.height;
                    var ctx = c.getContext('2d');
                    ctx.drawImage(img, 0, 0,c.width,c.height);
                    extend(atob(c.toDataURL('image/jpeg').split(',')[1]),c.width,c.height)
                break;
                case'b64':
                    base64 = e.mon.last_frame.split(',')[1];
                    var image_data = new Image();
                    image_data.src = base64;
                    extend(atob(base64),image_data.width,image_data.height)
                break;
                case'jpeg':
                    url=e.p.find('.stream-element').attr('src');
                    image_data = new Image();
                    image_data.src = url;
                    finish(url,image_data,image_data.width,image_data.height);
                break;
            }
        }else{
            url=e.p.find('.stream-element').attr('src');
            image_data = new Image();
            image_data.src = url;
            cb(url,image_data,image_data.width,image_data.height);
        }
    }
    $.ccio.snapshotVideo=function(videoElement,cb){
        var image_data;
        var base64
        $('#temp').html('<canvas></canvas>')
        var c = $('#temp canvas')[0];
        var img = videoElement;
        c.width = img.videoWidth;
        c.height = img.videoHeight;
        var ctx = c.getContext('2d');
        ctx.drawImage(img, 0, 0,c.width,c.height);
        base64=c.toDataURL('image/jpeg')
        image_data=atob(base64.split(',')[1]);
        var arraybuffer = new ArrayBuffer(image_data.length);
        var view = new Uint8Array(arraybuffer);
        for (var i=0; i<image_data.length; i++) {
            view[i] = image_data.charCodeAt(i) & 0xff;
        }
        try {
            var blob = new Blob([arraybuffer], {type: 'application/octet-stream'});
        } catch (e) {
            var bb = new (window.WebKitBlobBuilder || window.MozBlobBuilder);
            bb.append(arraybuffer);
            var blob = bb.getBlob('application/octet-stream');
        }
        cb(base64,image_data,c.width,c.height);
    }
    $.ccio.magnifyStream = function(e){
        if(!e.p){
            e.e=$(this),
            e.p=e.e.parents('[mid]')
        }
        if(e.animate === true){
            var zoomGlassAnimate = 'animate'
        }else{
            var zoomGlassAnimate = 'css'
        }
        if(e.auto === true){
            var streamBlockOperator = 'position'
        }else{
            var streamBlockOperator = 'offset'
        }
        if(e.useCanvas === true){
            var magnifiedElement = 'canvas'
        }else{
            var magnifiedElement = 'iframe'
        }
        e.ke=e.p.attr('ke'),//group key
        e.mid=e.p.attr('mid'),//monitor id
        e.auth=e.p.attr('auth'),//authkey
        e.mon=$.ccio.mon[e.ke+e.mid+e.auth]//monitor configuration
        if(e.zoomAmount)e.mon.zoomAmount=3;
        if(!e.mon.zoomAmount)e.mon.zoomAmount=3;
        e.height=parseFloat(e.p.attr('realHeight')) * e.mon.zoomAmount//height of stream
        e.width=parseFloat(e.p.attr('realWidth')) * e.mon.zoomAmount;//width of stream
        var targetForZoom = e.p.find('.stream-element');
        zoomGlass = e.p.find(".zoomGlass");
        var zoomFrame = function(){
            var magnify_offset = e.p.find('.stream-block')[streamBlockOperator]();
            var mx = e.pageX - magnify_offset.left;
            var my = e.pageY - magnify_offset.top;
            var rx = Math.round(mx/targetForZoom.width()*e.width - zoomGlass.width()/2)*-1;
            var ry = Math.round(my/targetForZoom.height()*e.height - zoomGlass.height()/2)*-1;
            var px = mx - zoomGlass.width()/2;
            var py = my - zoomGlass.height()/2;
            zoomGlass[zoomGlassAnimate]({left: px, top: py}).find(magnifiedElement)[zoomGlassAnimate]({left: rx, top: ry});
        }
        if(!e.height||!e.width||zoomGlass.length===0){
            $.ccio.snapshot(e,function(url,buffer,width,height){
                e.width = width * e.mon.zoomAmount;
                e.height = height * e.mon.zoomAmount;
                e.p.attr('realWidth',width)
                e.p.attr('realHeight',height)
                zoomGlass = e.p.find(".zoomGlass");
                if(zoomGlass.length===0){
                    if(e.useCanvas === true){
                        e.p.append('<div class="zoomGlass"><canvas class="blenderCanvas"></canvas></div>');
                    }else{
                        e.p.append('<div class="zoomGlass"><iframe src="/'+e.auth+'/embed/'+e.ke+'/'+e.mid+'/fullscreen|jquery|relative"/><div class="hoverShade"></div></div>');
                    }
                    zoomGlass = e.p.find(".zoomGlass");
                }
                zoomGlass.find(magnifiedElement).css({height:e.height,width:e.width});
                zoomFrame()
            })
        }else{
            zoomGlass.find(magnifiedElement).css({height:e.height,width:e.width});
            zoomFrame()
        }
    }
    $.ccio.tm=function(x,d,z,user){
        var tmp='';if(!d){d={}};
        var k={}
        if(d&&d.user){
            user=d.user
        }
        if(!user){
            user=$user
        }
        if(d.id&&!d.mid){d.mid=d.id;}
        switch(x){
            case 0://video
                if(!d.href&&d.hrefNoAuth){d.href=$.ccio.init('location',user)+user.auth_token+d.hrefNoAuth}
                if(user!==$user&&d.href.charAt(0)==='/'){
                    d.href=$.ccio.init('location',user)+(d.href.substring(1))
                }
                if(!d.filename){d.filename=$.ccio.init('tf',d.time)+'.'+d.ext;}
                d.dlname=d.mid+'-'+d.filename;
                d.mom=moment(d.time),
                d.hr=parseInt(d.mom.format('HH')),
                d.per=parseInt(d.hr/24*100);
                d.href='href="'+d.href+'?downloadName='+d.mid+'-'+d.filename+'"';
                d.circle='<div title="at '+d.hr+' hours of '+d.mom.format('MMMM DD')+'" '+d.href+' video="launch" class="progress-circle progress-'+d.per+'"><span>'+d.hr+'</span></div>'
                tmp+='<li class="glM'+d.mid+user.auth_token+'" auth="'+user.auth_token+'" mid="'+d.mid+'" ke="'+d.ke+'" status="'+d.status+'" status="'+d.status+'" file="'+d.filename+'">'+d.circle+'<div><span title="'+d.end+'" class="livestamp"></span></div><div><div class="small"><b><%-cleanLang(lang.Start)%></b> : '+moment(d.time).format('h:mm:ss , MMMM Do YYYY')+'</div><div class="small"><b><%-cleanLang(lang.End)%></b> : '+moment(d.end).format('h:mm:ss , MMMM Do YYYY')+'</div></div><div><span class="pull-right">'+(parseInt(d.size)/1000000).toFixed(2)+'mb</span><div class="controls btn-group"><a class="btn btn-sm btn-primary" video="launch" '+d.href+'><i class="fa fa-play-circle"></i></a> <a download="'+d.dlname+'" '+d.href+' class="btn btn-sm btn-default"><i class="fa fa-download"></i></a>'
                <% if(config.DropboxAppKey){ %> tmp+='<a video="download" host="dropbox" download="'+d.dlname+'" '+d.href+' class="btn btn-sm btn-default"><i class="fa fa-dropbox"></i></a>' <% } %>
                tmp+='<a title="<%-cleanLang(lang['Delete Video'])%>" video="delete" class="btn btn-sm btn-danger permission_video_delete"><i class="fa fa-trash"></i></a></div></div></li>';
            break;
            case 1://monitor icon
                d.src=placeholder.getData(placeholder.plcimg({bgcolor:'#b57d00',text:'...'}));
                tmp+='<div auth="'+user.auth_token+'" mid="'+d.mid+'" ke="'+d.ke+'" title="'+d.mid+' : '+d.name+'" class="monitor_block glM'+d.mid+user.auth_token+' col-md-4"><img monitor="watch" class="snapshot" src="'+d.src+'"><div class="box"><div class="title monitor_name truncate">'+d.name+'</div><div class="list-data"><div class="monitor_mid">'+d.mid+'</div><div><b><%-cleanLang(lang['Save as'])%> :</b> <span class="monitor_ext">'+d.ext+'</span></div><div><b>Mode :</b> <span class="monitor_mode">'+d.mode+'</span></div></div><div class="icons text-center"><div class="btn-group"><a class="btn btn-xs btn-default permission_monitor_edit" monitor="edit"><i class="fa fa-wrench"></i></a> <a monitor="videos_table" class="btn btn-xs btn-default"><i class="fa fa-film"></i></a> <a monitor="pop" class="btn btn-xs btn-success"><i class="fa fa-external-link"></i></a></div></div></div></div>';
                delete(d.src);
            break;
            case 2://monitor stream
                try{k.d=JSON.parse(d.details);}catch(er){k.d=d.details;}
                k.mode=$.ccio.init('humanReadMode',d.mode);
                var dataTarget = '.monitor_item[mid=\''+d.mid+'\'][ke=\''+d.ke+'\'][auth=\''+user.auth_token+'\']';
                tmp+='<div auth="'+user.auth_token+'" mid="'+d.mid+'" ke="'+d.ke+'" id="monitor_live_'+d.mid+user.auth_token+'" mode="'+k.mode+'" class="monitor_item glM'+d.mid+user.auth_token+' mdl-grid col-md-6">';
                tmp+='<div class="mdl-card mdl-cell mdl-cell--8-col">';
                tmp+='<div class="stream-block no-padding mdl-card__media mdl-color-text--grey-50">';
                tmp+='<div class="stream-objects"></div>';
                tmp+='<div class="stream-hud"><div class="lamp" title="'+k.mode+'"><i class="fa fa-eercast"></i></div><div class="controls"><span title="<%-cleanLang(lang['Currently viewing'])%>" class="label label-default"><span class="viewers"></span></span> <a class="btn-xs btn-danger btn" monitor="mode" mode="record"><i class="fa fa-circle"></i> <%-cleanLang(lang['Start Recording'])%></a> <a class="btn-xs btn-primary btn" monitor="mode" mode="start"><i class="fa fa-eye"></i> <%-cleanLang(lang['Set to Watch Only'])%></a></div><div class="bottom-text monospace"><div class="detector-fade">'
                    $.each([
                        {label:'Currently Detected',tag:'stream-detected-count'}
                    ],function(n,v){
                        tmp+='<div>'+v.label+' : <span class="'+v.tag+'"></span></div>'
                    })
                tmp+='</div></div></div></div>';
                tmp+='<div class="mdl-card__supporting-text text-center">';
                tmp+='<div class="indifference detector-fade"><div class="progress"><div class="progress-bar progress-bar-danger" role="progressbar"><span></span></div></div></div>';
                tmp+='<div class="monitor_details">';
                tmp+='<div><span class="monitor_name">'+d.name+'</span><span class="monitor_not_record_copy">, <%-cleanLang(lang['Recording FPS'])%> : <span class="monitor_fps">'+d.fps+'</span></span></div>';
                tmp+='</div>';
                tmp+='<div class="btn-group btn-group-sm">'//start of btn list
                    $.each([
                        {label:"<%-cleanLang(lang.Snapshot)%>",attr:'monitor="snapshot"',class:'primary',icon:'camera'},
                        {label:"<%-cleanLang(lang['Show Logs'])%>",attr:'class_toggle="show_logs" data-target="'+dataTarget+'"',class:'warning',icon:'exclamation-triangle'},
                        {label:"<%-cleanLang(lang.Control)%>",attr:'monitor="control_toggle"',class:'default arrows'},
                        {label:"<%-cleanLang(lang['Status Indicator'])%>",attr:'monitor="watch_on"',class:'success signal',icon:'plug'},
                        {label:"<%-cleanLang(lang['Detector'])%>",attr:'monitor="motion"',class:'warning',icon:'grav'},
                        {label:"<%-cleanLang(lang.Pop)%>",attr:'monitor="pop"',class:'default',icon:'external-link'},
//                        {label:"<%-cleanLang(lang.Magnify)%>",attr:'monitor="magnify"',class:'default',icon:'search-plus'},
                        {label:"<%-cleanLang(lang.Calendar)%>",attr:'monitor="calendar"',class:'default',icon:'calendar'},
                        {label:"<%-cleanLang(lang['Power Viewer'])%>",attr:'monitor="powerview"',class:'default',icon:'map-marker'},
                        {label:"<%-cleanLang(lang['Time-lapse'])%>",attr:'monitor="timelapse"',class:'default',icon:'angle-double-right'},
                        {label:"<%-cleanLang(lang['Videos List'])%>",attr:'monitor="videos_table"',class:'default',icon:'film'},
                        {label:"<%-cleanLang(lang['Monitor Settings'])%>",attr:'monitor="edit"',class:'default permission_monitor_edit',icon:'wrench'},
                        {label:"<%-cleanLang(lang.Fullscreen)%>",attr:'monitor="fullscreen"',class:'default',icon:'arrows-alt'},
                        {label:"<%-cleanLang(lang.Close)%>",attr:'monitor="watch_off"',class:'danger',icon:'times'},
                    ],function(n,v){
                        tmp+='<a class="btn btn-'+v.class+'" '+v.attr+' title="'+v.label+'"><i class="fa fa-'+v.icon+'"></i></a>'
                    })
                tmp+='</div>';//end of btn list
                tmp+='</div>';
                tmp+='</div>';
                tmp+='<div class="mdl-card mdl-cell mdl-cell--8-col mdl-cell--4-col-desktop">';
                tmp+='<div class="mdl-card__media">';
                tmp+='<div class="side-menu logs scrollable"></div>';
                tmp+='<div class="side-menu videos_monitor_list glM'+d.mid+user.auth_token+' scrollable"><ul></ul></div>';
                tmp+='</div>';
                tmp+='<div class="mdl-card__supporting-text meta meta--fill mdl-color-text--grey-600">';
                tmp+='<div><span class="monitor_name">'+d.name+'</span><span class="monitor_not_record_copy"><%-cleanLang(lang['Recording FPS'])%> : <b class="monitor_fps">'+d.fps+'</b></span>';
                tmp+='<b class="monitor_mode">'+k.mode+'</b>';
                tmp+='</div>';
                tmp+='</div>';
                tmp+='</div>';
            break;
            case 3://api key row
                tmp+='<tr api_key="'+d.code+'"><td class="code">'+d.code+'</td><td class="ip">'+d.ip+'</td><td class="time">'+d.time+'</td><td class="text-right"><a class="delete btn btn-xs btn-danger">&nbsp;<i class="fa fa-trash"></i>&nbsp;</a></td></tr>';
            break;
            case 4://log row, draw to global and monitor
                if(!d.time){d.time=$.ccio.init('t')}
                tmp+='<li class="log-item">'
                tmp+='<span>'
                tmp+='<div>'+d.ke+' : <b>'+d.mid+'</b></div>'
                tmp+='<span>'+d.log.type+'</span> '
                tmp+='<b class="time livestamp" title="'+d.time+'"></b>'
                tmp+='</span>'
                tmp+='<div class="message">'
                tmp+=$.ccio.init('jsontoblock',d.log.msg);
                tmp+='</div>'
                tmp+='</li>';
                $(z).each(function(n,v){
                    v=$(v);
                    if(v.find('.log-item').length>10){v.find('.log-item:last').remove()}
                })
            break;
            case 6://notification row
                if(!d.time){d.time=$.ccio.init('t')}
                if(!d.note.class){d.note.class=''}
                tmp+='<li class="note-item '+d.note.class+'" ke="'+d.ke+'" auth="'+user.auth_token+'" mid="'+d.id+'">'
                tmp+='<span>'
                tmp+='<div>'+d.ke+' : <b>'+d.id+'</b></div>'
                tmp+='<span>'+d.note.type+'</span> '
                tmp+='<b class="time livestamp" title="'+d.time+'"></b>'
                tmp+='</span>'
                tmp+='<div class="message">'
                tmp+=d.note.msg
                tmp+='</div>'
                tmp+='</li>';
            break;
            case'option':
                tmp+='<option auth="'+user.auth_token+'" value="'+d.id+'">'+d.name+'</option>'
            break;
            case'stream-element':
                try{k.d=JSON.parse(d.details);}catch(er){k.d=d.details}
                if($.ccio.mon[d.ke+d.mid+user.auth_token]&&$.ccio.mon[d.ke+d.mid+user.auth_token].previousStreamType===k.d.stream_type){
                    return;
                }
                k.e=$('#monitor_live_'+d.mid+user.auth_token+' .stream-block');
                k.e.find('.stream-element').remove();
                if($.ccio.op().jpeg_on===true){
                    tmp+='<img class="stream-element">';
                }else{
                    switch(k.d.stream_type){
                        case'hls':case'flv':case'mp4':
                            tmp+='<video class="stream-element" autoplay></video>';
                        break;
                        case'mjpeg':
                            tmp+='<iframe class="stream-element"></iframe>';
                        break;
                        case'jpeg'://base64
                            tmp+='<img class="stream-element">';
                        break;
                        default://base64
                            tmp+='<canvas class="stream-element"></canvas>';
                        break;
                    }
                }
                k.e.append(tmp).find('.stream-element').resize();
            break;
            case'user-row':
                d.e=$('.user-row[uid="'+d.uid+'"][ke="'+d.ke+'"]')
                if(d.e.length===0){
                    tmp+='<li class="user-row" uid="'+d.uid+'" ke="'+d.ke+'">';
                    tmp+='<span><div><span class="mail">'+d.mail+'</span> : <b class="uid">'+d.uid+'</b></div><span>Logged in</span> <b class="time livestamped" title="'+d.logged_in_at+'"></b></span>';
                    tmp+='</li>';
                }else{
                    d.e.find('.mail').text(d.mail)
                    d.e.find('.time').livestamp('destroy').toggleClass('livestamped livestamp').text(d.logged_in_at)
                }
                $.ccio.init('ls')
            break;
            case'filters-where':
                if(!d)d={};
                d.id=$('#filters_where .row').length;
                if(!d.p1){d.p1='mid'}
                if(!d.p2){d.p2='='}
                if(!d.p3){d.p3=''}
                tmp+='<div class="row where-row">';
                tmp+='   <div class="form-group col-md-4">';
                tmp+='       <label>';
                tmp+='           <select class="form-control" where="p1">';
                tmp+='               <option value="mid" selected><%-cleanLang(lang['Monitor ID'])%></option>';
                tmp+='               <option value="ext"><%-cleanLang(lang['File Type'])%></option>';
                tmp+='               <option value="time"><%-cleanLang(lang['Start Time'])%></option>';
                tmp+='               <option value="end"><%-cleanLang(lang['End Time'])%></option>';
                tmp+='               <option value="size"><%-cleanLang(lang['Filesize'])%></option>';
                tmp+='               <option value="status"><%-cleanLang(lang['Video Status'])%></option>';
                tmp+='           </select>';
                tmp+='       </label>';
                tmp+='   </div>';
                tmp+='   <div class="form-group col-md-4">';
                tmp+='       <label>';
                tmp+='           <select class="form-control" where="p2">';
                tmp+='               <option value="=" selected><%-cleanLang(lang['Equal to'])%></option>';
                tmp+='               <option value="!="><%-cleanLang(lang['Not Equal to'])%></option>';
                tmp+='               <option value=">="><%-cleanLang(lang['Greater Than or Equal to'])%></option>';
                tmp+='               <option value=">"><%-cleanLang(lang['Greater Than'])%></option>';
                tmp+='               <option value="<"><%-cleanLang(lang['Less Than'])%></option>';
                tmp+='               <option value="<="><%-cleanLang(lang['Less Than or Equal to'])%></option>';
                tmp+='               <option value="LIKE"><%-cleanLang(lang['Like'])%></option>';
                tmp+='               <option value="=~"><%-cleanLang(lang['Matches'])%></option>';
                tmp+='               <option value="!~"><%-cleanLang(lang['Not Matches'])%></option>';
                tmp+='               <option value="=[]"><%-cleanLang(lang['In'])%></option>';
                tmp+='               <option value="![]"><%-cleanLang(lang['Not In'])%></option>';
                tmp+='           </select>';
                tmp+='       </label>';
                tmp+='   </div>';
                tmp+='   <div class="form-group col-md-4">';
                tmp+='       <label>';
                tmp+='           <input class="form-control" placeholder="Value" title="<%-cleanLang(lang.Value)%>" where="p3">';
                tmp+='       </label>';
                tmp+='   </div>';
                tmp+='</div>';
            break;
            case 'link-set'://Link Shinobi - 1 set
                if(!d.host){d.host=''}
                if(!d.ke){d.ke=''}
                if(!d.api){d.api=''}
                if(!d.secure){d.secure="0"}
                tmp+='<div class="linksGroup" links="'+d.host+'">'
                tmp+='<h4 class="round-left">'+d.host+' <small>'+d.ke+'</small>&nbsp;<div class="pull-right"><a class="btn btn-danger btn-xs delete"><i class="fa fa-trash-o"></i></a></div></h4>'
                tmp+='<div class="form-group"><label><div><span><%-lang.Host%></span></div><div><input class="form-control" link="host" value="'+d.host+'"></div></label></div>'
                tmp+='<div class="form-group"><label><div><span><%-lang['Group Key']%></span></div><div><input class="form-control" link="ke" value="'+d.ke+'"></div></label></div>'
                tmp+='<div class="form-group"><label><div><span><%-lang['API Key']%></span></div><div><input class="form-control" link="api" value="'+d.api+'"></div></label></div>'
                tmp+='<div class="form-group"><label><div><span><%-lang.Secure%> (HTTPS/WSS)</span></div><div><select class="form-control" link="secure"><option value="1"><%-lang.Yes%></option><option selected value="0"><%-lang.No%></option></select></div></label></div>'
                tmp+='</div>';
            break;
            case 'form-group'://Input Map Selector
                var fields = []
                if(d.fields){
                    if(d.fields instanceof Object){
                        fields = [d]
                    }else{
                        fields = d
                    }
                }
                $.each(fields,function(n,v){
                    var value,hidden
                    if(!v.attribute)v.attribute='';
                    if(!v.placeholder)v.placeholder='';
                    if(!v.class)v.class='';
                    if(!v.inputType)v.inputType='value';
                    if(v.hidden){hidden='style="display:none"'}else{hidden=''};
                    if(v.value){value='value=""'}else{value=''};
                    tmp+='     <div class="form-group '+v.class+'" '+hidden+'>'
                    tmp+='        <label><div><span>'+v.label+'</span></div>'
                    tmp+='            <div>'
                    switch(v.type){
                        case'text':
                        tmp+='<input class="form-control" '+v.inputType+'="'+v.name+'" placeholder="'+v.placeholder+'" "'+value+'" '+v.attribute+'>'
                        break;
                        case'selector':
                        tmp+='<select class="form-control" '+v.inputType+'="'+v.name+'" placeholder="'+v.placeholder+'" '+v.attribute+'>'
                        $.each(v.choices,function(m,b){
                            tmp+='<option value="'+b.value+'">'+b.label+'</option>'
                        })
                        tmp+='</select>'
                        break;
                    }
                    tmp+='            </div>'
                    tmp+='        </label>'
                    tmp+='      </div>'
                })
            break;
            case 'input-map-selector'://Input Map Selector
                if(!d.map){d.map=''}
                tmp+='     <div class="form-group map-row">'
                tmp+='        <label><div><span><%-cleanLang(lang['Map'])%></span></div>'
                tmp+='            <div>'
                tmp+='            <div class="input-group input-group-sm">'
                tmp+='<input class="form-control" map-input="map" value="'+d.map+'" placeholder="0">'
                tmp+='              <div class="input-group-btn">'
                tmp+='                  <a class="btn btn-danger delete_map_row">&nbsp;<i class="fa fa-trash-o"></i>&nbsp;</a>'
                tmp+='              </div>'
                tmp+='            </div>'
                tmp+='            </div>'
                tmp+='        </label>'
                tmp+='      </div>'
            break;
            case 'input-map'://Input Map Options
                var tempID = $.ccio.gid();
                if(!d.channel){
                    var numberOfChannelsDrawn = $('#monSectionInputMaps .input-map').length
                    d.channel=numberOfChannelsDrawn+1
                }
                var fields = [
//                    {
//                        name:'',
//                        class:'',
//                        placeholder:'',
//                        default:'',
//                        attribute:'',
//                        type:'text',
//                    },
                    {
                        name:'type',
                        label:'<%-cleanLang(lang['Input Type'])%>',
                        default:'h264',
                        attribute:'selector="h_i_'+tempID+'"',
                        type:'selector',
                        choices:[
                            {label:'<%-cleanLang(lang['H.264 / H.265 / H.265+'])%>',value:'h264'},
                            {label:'<%-cleanLang(lang['JPEG'])%>',value:'jpeg'},
                            {label:'<%-cleanLang(lang['MJPEG'])%>',value:'mjpeg'},
                            {label:'<%-cleanLang(lang['HLS (.m3u8)'])%>',value:'hls'},
                            {label:'<%-cleanLang(lang['MPEG-4 (.mp4 / .ts)'])%>',value:'mp4'},
                            {label:'<%-cleanLang(lang['Local'])%>',value:'local'},
                            {label:'<%-cleanLang(lang['Raw'])%>',value:'raw'},
                        ]
                    },
                    {
                        name:'fulladdress',
                        label:'<%-cleanLang(lang['Full URL Path'])%>',
                        placeholder:'Example : rtsp://admin:password@123.123.123.123/stream/1',
                        type:'text',
                    },
                    {
                        name:'aduration',
                        label:'<%-cleanLang(lang['Analyzation Duration'])%>',
                        placeholder:'Example : 1000000',
                        type:'text',
                    },
                    {
                        name:'probesize',
                        label:'<%-cleanLang(lang['Probe Size'])%>',
                        placeholder:'Example : 1000000',
                        type:'text',
                    },
                    {
                        name:'stream_loop',
                        label:'<%-cleanLang(lang['Loop Stream'])%>',
                        class:'h_i_'+tempID+'_input h_i_'+tempID+'_mp4 h_i_'+tempID+'_raw',
                        hidden:true,
                        default:'0',
                        type:'selector',
                        choices:[
                            {label:'No',value:'0'},
                            {label:'Yes',value:'1'}
                        ]
                    },
                    {
                        name:'rtsp_transport',
                        label:'<%-cleanLang(lang['RTSP Transport'])%>',
                        class:'h_i_'+tempID+'_input h_i_'+tempID+'_h264',
                        default:'0',
                        type:'selector',
                        choices:[
                            {label:'Auto',value:''},
                            {label:'TCP',value:'tcp'},
                            {label:'UDP',value:'udp'}
                        ]
                    },
                    {
                        name:'accelerator',
                        label:'<%-cleanLang(lang['Accelerator'])%>',
                        attribute:'selector="h_accel_'+tempID+'"',
                        default:'0',
                        type:'selector',
                        choices:[
                            {label:'No',value:'0'},
                            {label:'Yes',value:'1'},
                        ]
                    },
                    {
                        name:'hwaccel',
                        label:'<%-cleanLang(lang['hwaccel'])%>',
                        class:'h_accel_'+tempID+'_input h_accel_'+tempID+'_1',
                        hidden:true,
                        default:'',
                        type:'selector',
                        choices:[
                            {label:'<%-cleanLang(lang['Auto'])%>',value:''},
                            {label:'<%-cleanLang(lang['cuvid'])%>',value:'cuvid'},
                            {label:'<%-cleanLang(lang['vaapi'])%>',value:'vaapi'},
                            {label:'<%-cleanLang(lang['qsv'])%>',value:'qsv'},
                            {label:'<%-cleanLang(lang['vdpau'])%>',value:'vdpau'},
                            {label:'<%-cleanLang(lang['dxva2'])%>',value:'dxva2'},
                            {label:'<%-cleanLang(lang['vdpau'])%>',value:'vdpau'},
                            {label:'<%-cleanLang(lang['videotoolbox'])%>',value:'videotoolbox'},
                        ]
                    },
                    {
                        name:'hwaccel_vcodec',
                        label:'<%-cleanLang(lang['hwaccel_vcodec'])%>',
                        class:'h_accel_'+tempID+'_input h_accel_'+tempID+'_1',
                        hidden:true,
                        default:'auto',
                        type:'selector',
                        choices:[
                            {label:'<%-cleanLang(lang['Auto'])%>',value:'auto'},
                            {label:'<%-cleanLang(lang['h264_cuvid'])%>',value:'h264_cuvid',group:'NVIDIA'},
                            {label:'<%-cleanLang(lang['hevc_cuvid'])%>',value:'hevc_cuvid',group:'NVIDIA'},
                            {label:'<%-cleanLang(lang['mjpeg_cuvid'])%>',value:'mjpeg_cuvid',group:'NVIDIA'},
                            {label:'<%-cleanLang(lang['mpeg4_cuvid'])%>',value:'mpeg4_cuvid',group:'NVIDIA'},
                            {label:'<%-cleanLang(lang['h264_qsv'])%>',value:'h264_qsv',group:'QuickSync Video'},
                            {label:'<%-cleanLang(lang['hevc_qsv'])%>',value:'hevc_qsv',group:'QuickSync Video'},
                            {label:'<%-cleanLang(lang['mpeg2_qsv'])%>',value:'mpeg2_qsv',group:'QuickSync Video'},
                        ]
                    },
                    {
                        name:'hwaccel_device',
                        label:'<%-cleanLang(lang['hwaccel_device'])%>',
                        class:'h_accel_'+tempID+'_input h_accel_'+tempID+'_1',
                        hidden:true,
                        placeholder:'Example : /dev/dri/video0',
                        type:'text',
                    },
                ];
                tmp+='<div class="form-group-group forestgreen input-map" section id="monSectionMap'+tempID+'">'
                tmp+='  <h4><%-lang["Input"]%> <b><%-lang["Map"]%> : <span class="place">'+d.channel+'</span></b>'
                tmp+='  <div class="pull-right"><a class="btn btn-danger btn-xs delete"><i class="fa fa-trash-o"></i></a></div>'
                tmp+='  </h4>'
                $.each(fields,function(n,v){
                    if(!v.attribute)v.attribute='';
                    if(!v.placeholder)v.placeholder='';
                    if(!v.class)v.class='';
                    if(v.hidden){v.hidden='style="display:none"'}else{v.hidden=''};
                    tmp+='     <div class="form-group '+v.class+'" '+v.hidden+'>'
                    tmp+='        <label><div><span>'+v.label+'</span></div>'
                    tmp+='            <div>'
                    switch(v.type){
                        case'text':
                        tmp+='<input class="form-control" map-detail="'+v.name+'" placeholder="'+v.placeholder+'" '+v.attribute+'>'
                        break;
                        case'selector':
                        tmp+='<select class="form-control" map-detail="'+v.name+'" placeholder="'+v.placeholder+'" '+v.attribute+'>'
                            $.each(v.choices,function(m,b){
                                tmp+='<option value="'+b.value+'">'+b.label+'</option>'
                            })
                        tmp+='</select>'
                        break;
                    }
                    tmp+='            </div>'
                    tmp+='        </label>'
                    tmp+='      </div>'
                })
                tmp+='</div>'
            break;
            case 'stream-channel'://Stream Channel
                var tempID = $.ccio.gid();
                if(!d.channel){
                    var numberOfChannelsDrawn = $('#monSectionStreamChannels .stream-channel').length
                    d.channel=numberOfChannelsDrawn
                }
                tmp+='<div class="form-group-group blue stream-channel" section id="monSectionChannel'+tempID+'">'
                tmp+='  <h4><%-lang["Stream Channel"]%> <span class="place">'+d.channel+'</span>'
                tmp+='  <div class="pull-right"><a class="btn btn-danger btn-xs delete"><i class="fa fa-trash-o"></i></a></div>'
                tmp+='  </h4>'
//                tmp+='      <div class="form-group">'
//                tmp+='        <label><div><span><%-lang["Input Selector"]%></span></div>'
//                tmp+='            <div><input class="form-control" channel-detail="stream_map" placeholder="0"></div>'
//                tmp+='        </label>'
//                tmp+='      </div>'
                tmp+='<div class="form-group-group forestgreen" input-mapping="stream_channel-'+d.channel+'">'
                tmp+='    <h4><%-cleanLang(lang['Input Feed'])%>'
                tmp+='        <div class="pull-right">'
                tmp+='            <a class="btn btn-success btn-xs add_map_row"><i class="fa fa-plus-square-o"></i></a>'
                tmp+='        </div>'
                tmp+='    </h4>'
                tmp+='    <div class="choices"></div>'
                tmp+='</div>'
                tmp+='     <div class="form-group">'
                tmp+='        <label><div><span><%-lang["Stream Type"]%></span></div>'
                tmp+='            <div><select class="form-control" channel-detail="stream_type" selector="h_st_channel_'+tempID+'" triggerChange="#monSectionChannel'+tempID+' [channel-detail=stream_vcodec]">'
                tmp+='                <option value="mp4"><%-lang["Poseidon"]%></option>'
                tmp+='                <option value="rtmp"><%-lang["RTMP Stream"]%></option>'
                tmp+='                <option value="flv"><%-lang["FLV"]%></option>'
                tmp+='                <option value="h264"><%-lang["Raw H.264 Stream"]%></option>'
                tmp+='                <option value="hls"><%-lang["HLS (includes Audio)"]%></option>'
                tmp+='                <option value="mjpeg"><%-lang["MJPEG"]%></option>'
                tmp+='            </select></div>'
                tmp+='        </label>'
                tmp+='      </div>'
                tmp+='          <div class="h_st_channel_'+tempID+'_input h_st_channel_'+tempID+'_rtmp">'
                tmp+='              <div class="form-group">'
                tmp+='                <label><div><span><%-lang["Server URL"]%></span></div>'
                tmp+='                <div><input class="form-control" channel-detail="rtmp_server_url" placeholder="Example : rtmp://live-api.facebook.com:80/rtmp/"></div>'
                tmp+='                </label>'
                tmp+='              </div>'
                tmp+='              <div class="form-group">'
                tmp+='                <label><div><span><%-lang["Stream Key"]%></span></div>'
                tmp+='                <div><input class="form-control" channel-detail="rtmp_stream_key" placeholder="Example : 1111111111?ds=1&a=xxxxxxxxxx"></div>'
                tmp+='                </label>'
                tmp+='              </div>'
                tmp+='          </div>'
                tmp+='      <div class="form-group h_st_channel_'+tempID+'_input h_st_channel_'+tempID+'_mjpeg" style="display:none">'
                tmp+='        <label><div><span><%-lang["# of Allow MJPEG Clients"]%></span></div>'
                tmp+='            <div><input class="form-control" channel-detail="stream_mjpeg_clients" placeholder="20"></div>'
                tmp+='        </label>'
                tmp+='      </div>'
                tmp+='      <div class="h_st_channel_'+tempID+'_input h_st_channel_'+tempID+'_hls h_st_channel_'+tempID+'_rtmp h_st_channel_'+tempID+'_flv h_st_channel_'+tempID+'_mp4  h_st_channel_'+tempID+'_h264">'
                tmp+='          <div class="form-group">'
                tmp+='            <label><div><span><%-lang["HLS Video Encoder"]%></span></div>'
                tmp+='                <div><select class="form-control" channel-detail="stream_vcodec" selector="h_hls_v_channel_'+tempID+'">'
                tmp+='                    <option value="no" selected><%-lang["Auto"]%></option>'
                tmp+='                    <option value="libx264"><%-lang["libx264"]%></option>'
                tmp+='                    <option value="libx265"><%-lang["libx265"]%></option>'
                tmp+='                    <option value="copy" selected><%-lang["copy"]%></option>'
                tmp+='                    <optgroup label="<%-lang["Hardware Accelerated"]%>">'
                tmp+='                        <option value="h264_vaapi"><%-lang["h264_vaapi"]%></option>'
                tmp+='                        <option value="hevc_vaapi"><%-lang["hevc_vaapi"]%></option>'
                tmp+='                        <option value="h264_nvenc"><%-lang["h264_nvenc"]%></option>'
                tmp+='                        <option value="hevc_nvenc"><%-lang["hevc_nvenc"]%></option>'
                tmp+='                        <option value="h264_qsv"><%-lang["h264_qsv"]%></option>'
                tmp+='                        <option value="hevc_qsv"><%-lang["hevc_qsv"]%></option>'
                tmp+='                        <option value="mpeg2_qsv"><%-lang["mpeg2_qsv"]%></option>'
                tmp+='                    </optgroup>'
                tmp+='                </select></div>'
                tmp+='            </label>'
                tmp+='          </div>'
                tmp+='          <div class="form-group">'
                tmp+='            <label><div><span><%-lang["HLS Audio Encoder"]%></span></div>'
                tmp+='                <div><select class="form-control" channel-detail="stream_acodec">'
                tmp+='                    <option value="no" selected><%-lang["No Audio"]%></option>'
                tmp+='                    <option value=""><%-lang["Auto"]%></option>'
                tmp+='                    <option value="aac"><%-lang["aac"]%></option>'
                tmp+='                    <option value="ac3"><%-lang["ac3"]%></option>'
                tmp+='                    <option value="libmp3lame"><%-lang["libmp3lame"]%></option>'
                tmp+='                    <option value="copy"><%-lang["copy"]%></option>'
                tmp+='                </select></div>'
                tmp+='            </label>'
                tmp+='          </div>'
                tmp+='      </div>'
                tmp+='      <div class="h_st_channel_'+tempID+'_input h_st_channel_'+tempID+'_hls" style="display:none">'
                tmp+='          <div class="form-group">'
                tmp+='            <label><div><span><%-lang["HLS Segment Length"]%></span></div>'
                tmp+='                <div><input class="form-control" channel-detail="hls_time" placeholder="2"></div>'
                tmp+='            </label>'
                tmp+='          </div>'
                tmp+='          <div class="form-group">'
                tmp+='            <label><div><span><%-lang["HLS Preset"]%></span></div>'
                tmp+='                <div><input class="form-control" channel-detail="preset_stream" placeholder="ultrafast"></div>'
                tmp+='            </label>'
                tmp+='          </div>'
                tmp+='          <div class="form-group">'
                tmp+='            <label><div><span><%-lang["HLS List Size"]%></span></div>'
                tmp+='                <div><input class="form-control" channel-detail="hls_list_size" placeholder="2"></div>'
                tmp+='            </label>'
                tmp+='          </div>'
                tmp+='      </div>'
                tmp+='      <div class="h_st_channel_'+tempID+'_input h_st_channel_'+tempID+'_mjpeg h_st_channel_'+tempID+'_hls h_st_channel_'+tempID+'_rtmp h_st_channel_'+tempID+'_jsmpeg h_st_channel_'+tempID+'_flv h_st_channel_'+tempID+'_mp4  h_st_channel_'+tempID+'_h264 h_hls_v_channel_'+tempID+'_input h_hls_v_channel_'+tempID+'_libx264 h_hls_v_channel_'+tempID+'_libx265 h_hls_v_channel_'+tempID+'_h264_nvenc h_hls_v_channel_'+tempID+'_hevc_nvenc h_hls_v_channel_'+tempID+'_no" style="display:none">'
                tmp+='              <div class="form-group">'
                tmp+='                <label><div><span><%-lang["Quality"]%></span></div>'
                tmp+='                <div><input class="form-control" placeholder="23" channel-detail="stream_quality"></div>'
                tmp+='                </label>'
                tmp+='              </div>'
                tmp+='          <div class="h_st_channel_'+tempID+'_input h_st_channel_'+tempID+'_rtmp">'
                tmp+='              <div class="form-group">'
                tmp+='                <label><div><span><%-lang["Video Bit Rate"]%></span></div>'
                tmp+='                <div><input class="form-control" channel-detail="stream_v_br" placeholder=""></div>'
                tmp+='                </label>'
                tmp+='              </div>'
                tmp+='              <div class="form-group">'
                tmp+='                <label><div><span><%-lang["Audio Bit Rate"]%></span></div>'
                tmp+='                <div><input class="form-control" channel-detail="stream_a_br" placeholder="128k"></div>'
                tmp+='                </label>'
                tmp+='              </div>'
                tmp+='          </div>'
                tmp+='              <div class="form-group">'
                tmp+='                <label><div><span><%-lang["Rate"]%></span></div>'
                tmp+='                <div><input class="form-control" channel-detail="stream_fps" placeholder=""></div>'
                tmp+='                </label>'
                tmp+='              </div>'
                tmp+='              <div class="form-group">'
                tmp+='                <label><div><span><%-lang["Width"]%></span></div>'
                tmp+='                <div><input class="form-control" type="number" min="1" channel-detail="stream_scale_x" placeholder="Example : 640"></div>'
                tmp+='                </label>'
                tmp+='              </div>'
                tmp+='              <div class="form-group">'
                tmp+='                <label><div><span><%-lang["Height"]%></span></div>'
                tmp+='                <div><input class="form-control" type="number" min="1" channel-detail="stream_scale_y" placeholder="Example : 480"></div>'
                tmp+='                </label>'
                tmp+='              </div>'
                tmp+='          <div class="form-group">'
                tmp+='            <label><div><span><%-lang["Rotate"]%></span></div>'
                tmp+='                    <div><select class="form-control" channel-detail="rotate_stream">'
                tmp+='                        <option value="no" selected><%-lang["No Rotation"]%></option>'
                tmp+='                        <option value="2,transpose=2"><%-lang["180 Degrees"]%></option>'
                tmp+='                        <option value="0"><%-lang["90 Counter Clockwise and Vertical Flip (default)"]%></option>'
                tmp+='                        <option value="1"><%-lang["90 Clockwise"]%></option>'
                tmp+='                        <option value="2"><%-lang["90 Clockwise and Vertical Flip"]%></option>'
                tmp+='                        <option value="3"><%-lang["90 Clockwise and Vertical Flip"]%></option>'
                tmp+='                    </select></div>'
                tmp+='              </label>'
                tmp+='          </div>'
                tmp+='          <div class="form-group">'
                tmp+='            <label><div><span><%-lang["Video Filter"]%></span></div>'
                tmp+='            <div><input class="form-control" channel-detail="svf"></div>'
                tmp+='            </label>'
                tmp+='          </div>'
                tmp+='          <div class="form-group">'
                tmp+='              <label><div><span><%-lang["Stream Flags"]%></span></div>'
                tmp+='              <div><input class="form-control" channel-detail="cust_stream"></div>'
                tmp+='          </label>'
                tmp+='          </div>'
                tmp+='      </div>'
                tmp+='  </div>'
            break;
        }
        if(z){
            $(z).prepend(tmp)
        }
        switch(x){
            case 1:
                z='#monitors_list .link-monitors-list[auth="'+user.auth_token+'"][ke="'+d.ke+'"]'
                if($('.link-monitors-list[auth="'+user.auth_token+'"][ke="'+d.ke+'"]').length===0){
                    $("#monitors_list").append('<div class="link-monitors-list" auth="'+user.auth_token+'" ke="'+d.ke+'"></div>')
                    $(z).sortable({
                        handle:'.title',
                        update: function(event, ui) {
                            var arr=[]
                            $(z+" .monitor_block").each(function(n,v){
                                arr.push($(this).attr('mid'))
                            })
                            $user.details.monitorOrder=arr;
                            $.ccio.cx({f:'monitorOrder',monitorOrder:arr})
                            event.o=$.ccio.op().switches;
                            if(event.o&&event.o.monitorOrder===1){
                                $.ccio.init('monitorOrder',{no:['#monitors_list .link-monitors-list[auth="'+user.auth_token+'"][ke="'+d.ke+'"]']},user)
                            }
                        }
                    });
                }
                $(z).prepend(tmp)
            break;
            case 0:case 4:
                $.ccio.init('ls');
            break;
            case 2:
                k.e=$('#monitor_live_'+d.mid+user.auth_token);
                try{
                    if(JSON.parse(d.details).control=="1"){
                        k.e.find('[monitor="control_toggle"]').show()
                    }else{
                        k.e.find('.pad').remove();
                        k.e.find('[monitor="control_toggle"]').hide()
                    }
                    $.ccio.tm('stream-element',d,null,user)
                }catch(re){$.ccio.log(re)}
                k.mid=d.mid
                k.mon=$.ccio.mon[d.ke+d.mid+user.auth_token]
                $.ccio.init('monitorInfo',k)
            break;
            case'filters-where':
                $('#filters_where').append(tmp);
                $('#filters_where .row:last [where="p1"]').val(d.p1)
                $('#filters_where .row:last [where="p2"]').val(d.p2)
                $('#filters_where .row:last [where="p3"]').val(d.p3)
            break;
            case'input-map':
                var mapsList = $.aM.maps
                mapsList.append(tmp)
                mapsList.find('.input-map').last().find('[map-detail="aduration"]').change()
                return tempID;
            break;
            case'stream-channel':
                var channeList = $.aM.channels
                channeList.append(tmp)
                channeList.find('.stream-channel').last().find('[channel-detail="stream_vcodec"]').change()
                return tempID;
            break;
            case'link-set':
                $('[links="'+d.host+'"] [link="secure"]').val(d.secure).change()
            break;
        }
        return tmp;
    }
    $.ccio.pm=function(x,d,z,user){
        var tmp='';if(!d){d={}};
        if(!user){
            user=$user
        }
        switch(x){
            case 0:
                d.mon=$.ccio.mon[d.ke+d.mid+user.auth_token];
                d.ev='.glM'+d.mid+user.auth_token+'.videos_list ul,.glM'+d.mid+user.auth_token+'.videos_monitor_list ul';d.fr=$.ccio.fr.find(d.ev),d.tmp='';
                if(d.fr.length===0){$.ccio.fr.append('<div class="videos_list glM'+d.mid+user.auth_token+'"><h3 class="title">'+d.mon.name+'</h3><ul></ul></div>')}
                if(d.videos&&d.videos.length>0){
                $.each(d.videos,function(n,v){
                    if(v.status!==0){
                        tmp+=$.ccio.tm(0,v,null,user)
                    }
                })
                }else{
                    $('.glM'+d.mid+user.auth_token+'.videos_list,.glM'+d.mid+user.auth_token+'.videos_monitor_list').appendTo($.ccio.fr)
                    tmp+='<li class="notice novideos">No videos</li>';
                }
                $(d.ev).html(tmp);
                $.ccio.init('ls');
            break;
            case 3:
                z='#api_list';
                $(z).empty();
                $.each(d,function(n,v){
                    tmp+=$.ccio.tm(3,v,null,user);
                })
            break;
            case'option':
                $.each(d,function(n,v){
                    tmp+=$.ccio.tm('option',v,null,user);
                })
            break;
            case'user-row':
                $.each(d,function(n,v){
                    tmp+=$.ccio.tm('user-row',v,null,user);
                })
                z='#users_online'
            break;
            case'link-set':
                $.sM.links.empty()
                $.each(d,function(n,v){
                    tmp+=$.ccio.tm('link-set',v,'#linkShinobi',user)
                })
            break;
        }
        if(z){
            $(z).prepend(tmp)
        }
        return tmp;
    }
    $.ccio.op=function(r,rr,rrr){
        if(!rrr){rrr={};};if(typeof rrr === 'string'){rrr={n:rrr}};if(!rrr.n){rrr.n='ShinobiOptions_'+location.host}
        ii={o:localStorage.getItem(rrr.n)};try{ii.o=JSON.parse(ii.o)}catch(e){ii.o={}}
        if(!ii.o){ii.o={}}
        if(r&&rr&&!rrr.x){
            ii.o[r]=rr;
        }
        switch(rrr.x){
            case 0:
                delete(ii.o[r])
            break;
            case 1:
                delete(ii.o[r][rr])
            break;
        }
        localStorage.setItem(rrr.n,JSON.stringify(ii.o))
        return ii.o
    }
//websocket functions
$.users={}
$.ccio.globalWebsocket=function(d,user){
    if(d.f!=='monitor_frame'&&d.f!=='os'&&d.f!=='video_delete'&&d.f!=='detector_trigger'&&d.f!=='detector_record_timeout_start'&&d.f!=='log'){$.ccio.log(d);}
    if(!user){
        user=$user
    }
    if(d.viewers){
        $('[ke="'+d.ke+'"][mid="'+d.id+'"][auth="'+user.auth_token+'"] .viewers').html(d.viewers);
    }
    switch(d.f){
        case'note':
            $.ccio.init('note',d.note);
        break;
        case'detector_trigger':
            d.e=$('.monitor_item[ke="'+d.ke+'"][mid="'+d.id+'"][auth="'+user.auth_token+'"]')
            if($.ccio.mon[d.ke+d.id+user.auth_token]&&d.e.length>0){
                if(d.details.plates&&d.details.plates.length>0){
                    console.log('licensePlateStream',d.id,d)
                }
                if(d.details.matrices&&d.details.matrices.length>0){
                    d.monitorDetails=JSON.parse($.ccio.mon[d.ke+d.id+user.auth_token].details)
                    d.stream=d.e.find('.stream-element')
                    d.streamObjects=d.e.find('.stream-objects')
                    $.ccio.init('drawMatrices',d)
                    d.e.find('.stream-detected-count').text(d.streamObjects.find('.stream-detected-object').length)
                }else{
                    d.e.find('.stream-detected-count').text(1)
                }
                if(d.details.points&&Object.keys(d.details.points).length>0){
                    d.monitorDetails=JSON.parse($.ccio.mon[d.ke+d.id+user.auth_token].details)
                    d.stream=d.e.find('.stream-element')
                    d.streamObjects=d.e.find('.stream-objects')
                    $.ccio.init('drawPoints',d)
                    d.e.find('.stream-detected-count').text(d.streamObjects.find('.stream-detected-point').length)
                }
                if(d.details.confidence){
                    d.tt=d.details.confidence;
                    if (d.tt > 100) { d.tt = 100; }
                    d.e.find('.indifference .progress-bar').css('width',d.tt + "%").find('span').text(d.details.confidence)
                }
                d.e.addClass('detector_triggered')
                clearTimeout($.ccio.mon[d.ke+d.id+user.auth_token].detector_trigger_timeout);
                $.ccio.mon[d.ke+d.id+user.auth_token].detector_trigger_timeout=setTimeout(function(){
                    $('.monitor_item[ke="'+d.ke+'"][mid="'+d.id+'"][auth="'+user.auth_token+'"]').removeClass('detector_triggered').find('.stream-detected-object,.stream-detected-point').remove()
                },5000);
            }
        break;
        case'init_success':
            $('#monitors_list .link-monitors-list[auth="'+user.auth_token+'"][ke="'+user.ke+'"]').empty();
            if(user===$user){
                d.chosen_set='watch_on'
            }else{
                d.chosen_set='watch_on_links'
            }
            d.o=$.ccio.op()[d.chosen_set];
            if(!d.o){d.o={}};
            $.getJSON($.ccio.init('location',user)+user.auth_token+'/monitor/'+user.ke,function(f,g){
                g=function(n,v){
                    $.ccio.mon[v.ke+v.mid+user.auth_token]=v;
                    v.user=user;
                    $.ccio.tm(1,v,null,user)
                    if(d.o[v.ke]&&d.o[v.ke][v.mid]===1){
                        $.ccio.cx({f:'monitor',ff:'watch_on',id:v.mid},user)
                    }
                }
                if(f.mid){
                    g(null,f)
                }else{
                    $.each(f,g);
                }
                if($.ccio.op().jpeg_on===true){
                    $.ccio.cx({f:'monitor',ff:'jpeg_on'},user)
                }
                $.gR.drawList();
                setTimeout(function(){$.ccio.init('monitorOrder',null,user)},300)
            })
            $.ccio.pm(3,d.apis,null,user);
            $('.os_platform').html(d.os.platform)
            $('.os_cpuCount').html(d.os.cpuCount)
            $('.os_totalmem').html((d.os.totalmem/1000000).toFixed(2))
            if(d.os.cpuCount>1){
                $('.os_cpuCount_trailer').html('s')
            }
        break;
        case'get_videos':
            $.ccio.pm(0,d,null,user)
        break;
        case'log':
            $.ccio.tm(4,d,'#logs,.monitor_item[mid="'+d.mid+'"][ke="'+d.ke+'"][auth="'+user.auth_token+'"] .logs',user)
        break;
        case'os'://indicator
            //cpu
            d.cpu=parseFloat(d.cpu).toFixed(0)+'%';
            $('.cpu_load .progress-bar').css('width',d.cpu);
            $('.cpu_load .percent').html(d.cpu);
            //ram
            d.ram=(100-parseFloat(d.ram)).toFixed(0)+'%';
            $('.ram_load .progress-bar').css('width',d.ram);
            $('.ram_load .percent').html(d.ram);
        break;
        case'diskUsed':
            if(!d.limit||d.limit===''){d.limit=10000}
            d.percent=parseInt((d.size/d.limit)*100)+'%';
            d.human=parseFloat(d.size)
            if(d.human>1000){d.human=(d.human/1000).toFixed(2)+' GB'}else{d.human=d.human.toFixed(2)+' MB'}
            $('.diskUsed .value').html(d.human)
            $('.diskUsed .percent').html(d.percent)
            $('.diskUsed .progress-bar').css('width',d.percent)
        break;
        case'video_fix_success':case'video_fix_start':
            switch(d.f){
                case'video_fix_success':
                    d.addClass='fa-wrench'
                    d.removeClass='fa-pulse fa-spinner'
                break;
                case'video_fix_start':
                    d.removeClass='fa-wrench'
                    d.addClass='fa-pulse fa-spinner'
                break;
            }
            $('[mid="'+d.mid+'"][ke="'+d.ke+'"][file="'+d.filename+'"][auth="'+user.auth_token+'"] [video="fix"] i,[data-mid="'+d.mid+'"][data-ke="'+d.ke+'"][data-file="'+d.filename+'"][data-auth="'+user.auth_token+'"] [video="fix"] i').addClass(d.addClass).removeClass(d.removeClass)
        break;
        case'video_edit':case'video_archive':
            $.ccio.init('data-video',d)
            d.e=$('[file="'+d.filename+'"][mid="'+d.mid+'"][ke="'+d.ke+'"][auth="'+user.auth_token+'"]');
            d.e.attr('status',d.status),d.e.attr('data-status',d.status);
        break;
        case'video_delete':
            if($('.modal[mid="'+d.mid+'"][auth="'+user.auth_token+'"]').length>0){$('#video_viewer[mid="'+d.mid+'"]').attr('file',null).attr('ke',null).attr('mid',null).attr('auth',null).modal('hide')}
            $('[file="'+d.filename+'"][mid="'+d.mid+'"][ke="'+d.ke+'"][auth="'+user.auth_token+'"]').remove();
            $('[data-file="'+d.filename+'"][data-mid="'+d.mid+'"][data-ke="'+d.ke+'"][data-auth="'+user.auth_token+'"]').remove();
            if($.pwrvid.currentDataObject&&$.pwrvid.currentDataObject[d.filename]){
                delete($.timelapse.currentVideos[$.pwrvid.currentDataObject[d.filename].position])
                $.pwrvid.drawTimeline(false)
            }
            if($.timelapse.currentVideos&&$.timelapse.currentVideos[d.filename]){
                delete($.timelapse.currentVideosArray.videos[$.timelapse.currentVideos[d.filename].position])
                $.timelapse.drawTimeline(false)
            }
        break;
        case'video_build_success':
            if(!d.mid){d.mid=d.id;};d.status=1;
            d.e='.glM'+d.mid+user.auth_token+'.videos_list ul,.glM'+d.mid+user.auth_token+'.videos_monitor_list ul';$(d.e).find('.notice.novideos').remove();
            $.ccio.tm(0,d,d.e,user)
        break;
        case'monitor_snapshot':
            switch(d.snapshot_format){
                case'plc':
                    $('[mid="'+d.mid+'"][auth="'+user.auth_token+'"] .snapshot').attr('src',placeholder.getData(placeholder.plcimg(d.snapshot)))
                break;
                case'ab':
                    d.reader = new FileReader();
                    d.reader.addEventListener("loadend",function(){$('[mid="'+d.mid+'"][auth="'+user.auth_token+'"] .snapshot').attr('src',d.reader.result)});
                    d.reader.readAsDataURL(new Blob([d.snapshot],{type:"image/jpeg"}));
                break;
                case'b64':
                    $('[mid="'+d.mid+'"][ke="'+d.ke+'"][auth="'+user.auth_token+'"] .snapshot').attr('src','data:image/jpeg;base64,'+d.snapshot)
                break;
            }
        break;
        case'monitor_delete':
            $('[mid="'+d.mid+'"][ke="'+d.ke+'"][auth="'+user.auth_token+'"]:not(.modal)').remove();
            $.ccio.init('clearTimers',d)
            delete($.ccio.mon[d.ke+d.mid+user.auth_token]);
        break;
        case'monitor_watch_off':case'monitor_stopping':
            if(user===$user){
                d.chosen_set='watch_on'
            }else{
                d.chosen_set='watch_on_links'
            }
            d.o=$.ccio.op()[d.chosen_set];
            if(!d.o[d.ke]){d.o[d.ke]={}};d.o[d.ke][d.id]=0;$.ccio.op(d.chosen_set,d.o);
            if($.ccio.mon[d.ke+d.id+user.auth_token]){
                $.ccio.init('jpegModeStop',{mid:d.id,ke:d.ke});
                $.ccio.init('clearTimers',d)
                clearInterval($.ccio.mon[d.ke+d.id+user.auth_token].signal);delete($.ccio.mon[d.ke+d.id+user.auth_token].signal);
                $.ccio.mon[d.ke+d.id+user.auth_token].watch=0;
                if($.ccio.mon[d.ke+d.id+user.auth_token].hls){$.ccio.mon[d.ke+d.id+user.auth_token].hls.destroy()}
                if($.ccio.mon[d.ke+d.id+user.auth_token].dash){$.ccio.mon[d.ke+d.id+user.auth_token].dash.reset()}
                $('#monitor_live_'+d.id+user.auth_token).remove();
            }
        break;
        case'monitor_watch_on':
            if(user===$user){
                d.chosen_set='watch_on'
            }else{
                d.chosen_set='watch_on_links'
            }
            d.o=$.ccio.op()[d.chosen_set];
            if(!d.o){d.o={}};if(!d.o[d.ke]){d.o[d.ke]={}};d.o[d.ke][d.id]=1;$.ccio.op(d.chosen_set,d.o);
            $.ccio.mon[d.ke+d.id+user.auth_token].watch=1;
            delete($.ccio.mon[d.ke+d.id+user.auth_token].image)
            delete($.ccio.mon[d.ke+d.id+user.auth_token].ctx)
            d.e=$('#monitor_live_'+d.id+user.auth_token);
            d.e.find('.stream-detected-object').remove()
            $.ccio.init('clearTimers',d)
            if(d.e.length==0){
                $.ccio.tm(2,$.ccio.mon[d.ke+d.id+user.auth_token],'#monitors_live',user);
                $.ccio.init('dragWindows')
            }
            d.d=JSON.parse($.ccio.mon[d.ke+d.id+user.auth_token].details);
            $.ccio.tm('stream-element',$.ccio.mon[d.ke+d.id+user.auth_token],null,user);
            if($.ccio.op().jpeg_on===true){
                $.ccio.init('jpegMode',$.ccio.mon[d.ke+d.id+user.auth_token]);
            }else{
                var url = $.ccio.init('location',user);
                var prefix = 'ws'
                if(location.protocol==='https:'){
                    prefix = 'wss'
                }
                if(url=='/'){
                    url = prefix+'://'+location.host
                }else{
                    url = prefix+'://'+url.split('://')[1]
                }
                switch(d.d.stream_type){
                    case'jpeg':
                        $.ccio.init('jpegMode',$.ccio.mon[d.ke+d.id+user.auth_token]);
                    break;
                    case'mp4':
                        var stream = d.e.find('.stream-element');
                        if(d.d.stream_flv_type==='ws'){
                            if($.ccio.mon[d.ke+d.id+user.auth_token].Poseidon){
                                $.ccio.mon[d.ke+d.id+user.auth_token].Poseidon.destroy()
                            }
                            try{
                                $.ccio.mon[d.ke+d.id+user.auth_token].Poseidon = new Poseidon({
                                    video: stream[0],
                                    auth_token:user.auth_token,
                                    ke:d.ke,
                                    uid:user.uid,
                                    id:d.id,
                                    url: url
                                });
                                $.ccio.mon[d.ke+d.id+user.auth_token].Poseidon.start();
                            }catch(err){
                                setTimeout(function(){
                                    $.ccio.cx({f:'monitor',ff:'watch_on',id:d.id},user)
                                },3000)
                                console.log(err)
                            }
                        }else{
                            stream.attr('src',$.ccio.init('location',user)+user.auth_token+'/mp4/'+d.ke+'/'+d.id+'/s.mp4')
                            setTimeout(function(){
                                $.ccio.init('signal-check',{id:d.id,ke:d.ke})
                            },3000)
                        }
                    break;
                    case'flv':
                        if (flvjs.isSupported()) {
                            if($.ccio.mon[d.ke+d.id+user.auth_token].flv){
                                $.ccio.mon[d.ke+d.id+user.auth_token].flv.destroy()
                            }
                            var options = {};
                            if(d.d.stream_flv_type==='ws'){
                                if(d.d.stream_flv_maxLatency&&d.d.stream_flv_maxLatency!==''){
                                    d.d.stream_flv_maxLatency = parseInt(d.d.stream_flv_maxLatency)
                                }else{
                                    d.d.stream_flv_maxLatency = 20000;
                                }
                                options = {
                                    type: 'flv',
                                    isLive: true,
                                    auth_token:user.auth_token,
                                    ke:d.ke,
                                    uid:user.uid,
                                    id:d.id,
                                    maxLatency:d.d.stream_flv_maxLatency,
                                    hasAudio:false,
                                    url: url
                                }
                            }else{
                                options = {
                                    type: 'flv',
                                    isLive: true,
                                    url: $.ccio.init('location',user)+user.auth_token+'/flv/'+d.ke+'/'+d.id+'/s.flv'
                                }
                            }
                            $.ccio.mon[d.ke+d.id+user.auth_token].flv = flvjs.createPlayer(options);
                            $.ccio.mon[d.ke+d.id+user.auth_token].flv.attachMediaElement($('#monitor_live_'+d.id+user.auth_token+' .stream-element')[0]);
                            $.ccio.mon[d.ke+d.id+user.auth_token].flv.on('error',function(err){
                                console.log(err)
                            });
                            $.ccio.mon[d.ke+d.id+user.auth_token].flv.load();
                            $.ccio.mon[d.ke+d.id+user.auth_token].flv.play();
                        }else{
                            $.ccio.init('note',{title:'Stream cannot be started',text:'FLV.js is not supported on this browser. Try another stream type.',type:'error'});
                        }
                    break;
                    case'hls':
                        d.fn=function(){
                            clearTimeout($.ccio.mon[d.ke+d.id+user.auth_token].m3uCheck)
                            d.url=$.ccio.init('location',user)+user.auth_token+'/hls/'+d.ke+'/'+d.id+'/s.m3u8';
                            $.get(d.url,function(m3u){
                                if(m3u=='File Not Found'){
                                    $.ccio.mon[d.ke+d.id+user.auth_token].m3uCheck=setTimeout(function(){
                                        d.fn()
                                    },2000)
                                }else{
                                    var video = $('#monitor_live_'+d.id+user.auth_token+' .stream-element')[0];
                                    if (navigator.userAgent.match(/(iPod|iPhone|iPad)/)||(navigator.userAgent.match(/(Safari)/)&&!navigator.userAgent.match('Chrome'))) {
                                        video.src=d.url;
                                        if (video.paused) {
                                            video.play();
                                        }
                                    }else{
                                        $.ccio.mon[d.ke+d.id+user.auth_token].hlsGarbageCollector=function(){
                                            if($.ccio.mon[d.ke+d.id+user.auth_token].hls){$.ccio.mon[d.ke+d.id+user.auth_token].hls.destroy();URL.revokeObjectURL(video.src)}
                                            $.ccio.mon[d.ke+d.id+user.auth_token].hls = new Hls();
                                            $.ccio.mon[d.ke+d.id+user.auth_token].hls.loadSource(d.url);
                                            $.ccio.mon[d.ke+d.id+user.auth_token].hls.attachMedia(video);
                                            $.ccio.mon[d.ke+d.id+user.auth_token].hls.on(Hls.Events.MANIFEST_PARSED,function() {
                                                if (video.paused) {
                                                    video.play();
                                                }
                                            });
                                        }
                                        $.ccio.mon[d.ke+d.id+user.auth_token].hlsGarbageCollector()
                                        $.ccio.mon[d.ke+d.id+user.auth_token].hlsGarbageCollectorTimer=setInterval($.ccio.mon[d.ke+d.id+user.auth_token].hlsGarbageCollector,1000*60*20)
                                    }
                                }
                            })
                        }
                        d.fn()
                    break;
                    case'mjpeg':
                        $('#monitor_live_'+d.id+user.auth_token+' .stream-element').attr('src',user.auth_token+'/mjpeg/'+d.ke+'/'+d.id+'/?full=true')
                    break;
                }
            }
            d.signal=parseFloat(d.d.signal_check);
            if(!d.signal||d.signal==NaN){d.signal=10;};d.signal=d.signal*1000*60;
            if(d.signal>0){
                $.ccio.mon[d.ke+d.id+user.auth_token].signal=setInterval(function(){$.ccio.init('signal-check',{id:d.id,ke:d.ke})},d.signal);
            }
            d.e=$('.monitor_item[mid="'+d.id+'"][ke="'+d.ke+'"][auth="'+user.auth_token+'"]').resize()
            if(d.e.find('.videos_monitor_list li').length===0){
                d.dr=$('#videos_viewer_daterange').data('daterangepicker');
                $.getJSON($.ccio.init('location',user)+user.auth_token+'/videos/'+d.ke+'/'+d.id+'?limit=10',function(f){
                    $.ccio.pm(0,{videos:f.videos,ke:d.ke,mid:d.id},null,user)
                })
            }
            $.ccio.init('montage');
            setTimeout(function(){
                if($.ccio.mon[d.ke+d.id+user.auth_token].motionDetectionRunning===true){
                    $.ccio.init('streamMotionDetectRestart',{mid:d.id,ke:d.ke,mon:$.ccio.mon[d.ke+d.id+user.auth_token]},user);
                }
            },3000)
        break;
        case'monitor_frame':
            try{
                if(!$.ccio.mon[d.ke+d.id+user.auth_token].ctx||$.ccio.mon[d.ke+d.id+user.auth_token].ctx.length===0){
                    $.ccio.mon[d.ke+d.id+user.auth_token].ctx = $('#monitor_live_'+d.id+user.auth_token+' canvas');
                }
                if(!$.ccio.mon[d.ke+d.id+user.auth_token].image){
                    $.ccio.mon[d.ke+d.id+user.auth_token].image = new Image();
                    $.ccio.mon[d.ke+d.id+user.auth_token].image.onload = function() {
//                        d.x = 0,d.y = 0;
//                        d.ratio = Math.min($.ccio.mon[d.ke+d.id+user.auth_token].ctx.width()/$.ccio.mon[d.ke+d.id+user.auth_token].image.width,$.ccio.mon[d.ke+d.id+user.auth_token].ctx.height()/$.ccio.mon[d.ke+d.id+user.auth_token].image.height);
//                        d.height = $.ccio.mon[d.ke+d.id+user.auth_token].image.height*d.ratio;
//                        d.width = $.ccio.mon[d.ke+d.id+user.auth_token].image.width*d.ratio;
//                        if( d.width < $.ccio.mon[d.ke+d.id+user.auth_token].ctx.width() )
//                            d.x = ($.ccio.mon[d.ke+d.id+user.auth_token].ctx.width() / 2) - (d.width / 2);
//                        if( d.height < $.ccio.mon[d.ke+d.id+user.auth_token].ctx.height() )
//                            d.y = ($.ccio.mon[d.ke+d.id+user.auth_token].ctx.height() / 2) - (d.height / 2);
//                        $.ccio.mon[d.ke+d.id+user.auth_token].ctx[0].getContext("2d").drawImage($.ccio.mon[d.ke+d.id+user.auth_token].image,0,0,$.ccio.mon[d.ke+d.id+user.auth_token].image.width,$.ccio.mon[d.ke+d.id+user.auth_token].image.height,d.x,d.y,d.width,d.height);
                       
                        d.height=$.ccio.mon[d.ke+d.id+user.auth_token].ctx.height()
                        d.width=$.ccio.mon[d.ke+d.id+user.auth_token].ctx.width()
                        $.ccio.mon[d.ke+d.id+user.auth_token].ctx[0].getContext("2d").drawImage($.ccio.mon[d.ke+d.id+user.auth_token].image,0,0,d.width,d.height);
                    };
                }
                $.ccio.mon[d.ke+d.id+user.auth_token].image.src='data:image/jpeg;base64,'+d.frame;
                $.ccio.mon[d.ke+d.id+user.auth_token].last_frame='data:image/jpeg;base64,'+d.frame;
            }catch(er){
                console.log(er)
                $.ccio.log('base64 frame')
            }
            $.ccio.init('signal',d);
        break;
        case'monitor_edit':
            $.ccio.init('clearTimers',d)
            d.e=$('[mid="'+d.mon.mid+'"][ke="'+d.mon.ke+'"][auth="'+user.auth_token+'"]');
            d.e=$('#monitor_live_'+d.mid+user.auth_token);
            d.e.find('.stream-detected-object').remove()
            if(d.mon.details.control=="1"){d.e.find('[monitor="control_toggle"]').show()}else{d.e.find('.pad').remove();d.e.find('[monitor="control_toggle"]').hide()}
            if(user===$user){
                d.chosen_set='watch_on'
            }else{
                d.chosen_set='watch_on_links'
            }
            d.o=$.ccio.op()[d.chosen_set];
            if(!d.o){d.o={}}
            if(d.mon.details.cords instanceof Object){d.mon.details.cords=JSON.stringify(d.mon.details.cords);}
            d.mon.details=JSON.stringify(d.mon.details);
            if(!$.ccio.mon[d.ke+d.mid+user.auth_token]){$.ccio.mon[d.ke+d.mid+user.auth_token]={}}
            $.ccio.init('jpegModeStop',d);
            $.ccio.mon[d.ke+d.mid+user.auth_token].previousStreamType=d.mon.details.stream_type
            $.each(d.mon,function(n,v){
                $.ccio.mon[d.ke+d.mid+user.auth_token][n]=v;
            });
            $.ccio.mon[d.ke+d.mid+user.auth_token].user=user
            if(d.new===true){$.ccio.tm(1,d.mon,null,user)}
            switch(d.mon.mode){
                case'start':case'record':
                    if(d.o[d.ke]&&d.o[d.ke][d.mid]===1){
                        $.ccio.cx({f:'monitor',ff:'watch_on',id:d.mid},user)
                    }
                break;
            }
            $.ccio.init('monitorInfo',d)
            $.gR.drawList();
            $.ccio.init('note',{title:'Monitor Saved',text:'<b>'+d.mon.name+'</b> <small>'+d.mon.mid+'</small> has been saved.',type:'success'});
        break;
        case'monitor_starting':
//            switch(d.mode){case'start':d.mode='Watch';break;case'record':d.mode='Record';break;}
//            $.ccio.init('note',{title:'Monitor Starting',text:'Monitor <b>'+d.mid+'</b> is now running in mode <b>'+d.mode+'</b>',type:'success'});
            d.e=$('#monitor_live_'+d.mid+user.auth_token)
            if(d.e.length>0){$.ccio.cx({f:'monitor',ff:'watch_on',id:d.mid},user)}
        break;
        case'mode_jpeg_off':
            $.ccio.op('jpeg_on',"0");
            $.each($.ccio.mon,function(n,v,x){
                $.ccio.init('jpegModeStop',v);
                if(v.watch===1){
                    $.ccio.cx({f:'monitor',ff:'watch_on',id:v.mid},user)
                }
            });
            $('body').removeClass('jpegMode')
        break;
        case'mode_jpeg_on':
            $.ccio.op('jpeg_on',true);
            $.ccio.init('jpegModeAll');
            $('body').addClass('jpegMode')
        break;
        case'drawPowerVideoMainTimeLine':
            var videos = d.videos;
            var events = d.events;
//            $.pwrvid.currentlyLoading = false
            $.pwrvid.currentVideos=videos
            $.pwrvid.currentEvents=events
            $.pwrvid.e.find('.loading').hide()
            $.pwrvid.e.find('.nodata').hide()
            //$.pwrvid.drawTimeLine
            if($.pwrvid.t&&$.pwrvid.t.destroy){$.pwrvid.t.destroy()}
            data={};
            $.each(videos.videos,function(n,v){
                if(!v||!v.mid){return}
                v.mon=$.ccio.mon[v.ke+v.mid+$user.auth_token];
                v.filename=$.ccio.init('tf',v.time)+'.'+v.ext;
                if(v.status>0){
        //                    data.push({src:v,x:v.time,y:moment(v.time).diff(moment(v.end),'minutes')/-1})
                    data[v.filename]={filename:v.filename,time:v.time,timeFormatted:moment(v.time).format('MM/DD/YYYY HH:mm'),endTime:v.end,close:moment(v.time).diff(moment(v.end),'minutes')/-1,motion:[],row:v,position:n}
                }
            });
            $.each(events,function(n,v){
                $.each(data,function(m,b){
                    if (moment(v.time).isBetween(moment(b.time).format(),moment(b.endTime).format())) {
                        data[m].motion.push(v)
                    }
                })
            });
            $.pwrvid.currentDataObject=data;
            if($.pwrvid.chart){
                $.pwrvid.d.empty()
                delete($.pwrvid.chart)
            }
            $.pwrvid.currentData=Object.values(data);
            if($.pwrvid.currentData.length>0){
                var labels=[]
                var Dataset1=[]
                var Dataset2=[]
                $.each(data,function(n,v){
                    labels.push(v.timeFormatted)
                    Dataset1.push(v.close)
                    Dataset2.push(v.motion.length)
                })
                $.pwrvid.d.html("<canvas></canvas>")
                var timeFormat = 'MM/DD/YYYY HH:mm';
                var color = Chart.helpers.color;
                Chart.defaults.global.defaultFontColor = '#fff';
                var config = {
                    type: 'bar',
                    data: {
                        labels: labels,
                        datasets: [{
                            type: 'line',
                            label: '<%-cleanLang(lang['Video and Time Span (Minutes)'])%>',
                            backgroundColor: color(window.chartColors.blue).alpha(0.2).rgbString(),
                            borderColor: window.chartColors.blue,
                            data: Dataset1,
                        }, {
                            type: 'bar',
                            showTooltip: false,
                            label: '<%-cleanLang(lang['Counts of Motion'])%>',
                            backgroundColor: color(window.chartColors.red).alpha(0.5).rgbString(),
                            borderColor: window.chartColors.red,
                            data:Dataset2,
                        }, ]
                    },
                    options: {
                         maintainAspectRatio: false,
                        title: {
                            fontColor: "white",
                            text:"<%-lang['Video Length (minutes) and Motion Count per video']%>"
                        },
                        tooltips: {
                            callbacks: {

                            },
                        },
                        scales: {
                            xAxes: [{
                                type: "time",
                                display: true,
                                time: {
                                    format: timeFormat,
                                    // round: 'day'
                                }
                            }],
                        },
                    }
                };

                var ctx = $.pwrvid.d.find('canvas')[0].getContext("2d");
                $.pwrvid.chart = new Chart(ctx, config);
                $.pwrvid.d.find('canvas').click(function(e) {
                    var target = $.pwrvid.chart.getElementsAtEvent(e)[0];
                    if(!target){return false}
                    target = $.pwrvid.currentData[target._index];
                    $.pwrvid.e.find('.temp').html('<li class="glM'+target.row.mid+$user.auth_token+'" mid="'+target.row.mid+'" ke="'+target.row.ke+'" status="'+target.row.status+'" file="'+target.row.filename+'" auth="'+$user.auth_token+'"><a class="btn btn-sm btn-primary" preview="video" href="'+target.row.href+'"><i class="fa fa-play-circle"></i></a></li>').find('a').click()
                });
                var colorNames = Object.keys(window.chartColors);
            }else{
                $.pwrvid.e.find('.nodata').show()
            }
        break;
    }
}
$user.ws=io(location.origin);
$user.ws.on('connect',function (d){
    $(document).ready(function(e){
        $.ccio.init('id',$user);
        $.ccio.cx({f:'init',ke:$user.ke,auth:$user.auth_token,uid:$user.uid})
        if($user.details&&$user.details.links){
            $.each($user.details.links,function(n,v){
                if(v.secure==='0'){
                    v.protocol='http'
                }else{
                    v.protocol='https'
                }
                if(v.host.indexOf('://')>-1){
                    v.URL=v.protocol+'://'+v.host.split('://')[1]
                }else{
                    v.URL=v.protocol+'://'+v.host
                }
                $.get(v.URL+'/'+v.api+'/userInfo/'+v.ke,function(e){
                    if(e.ok===true){
                        e.user.auth_token=v.api
                        $.users[v.api]=e.user
                        $.users[v.api].info=v
                        $.users[v.api].ws=io(v.host)
                        $.users[v.api].ws.on('ping', function(d){
                            $.users[v.api].ws.emit('pong',{beat:1});
                        });
                        $.users[v.api].ws.on('connect',function (d){
                            console.log(v.host,'connected')
                            $.ccio.cx({f:'init',ke:e.user.ke,auth:v.api,uid:e.user.uid},$.users[v.api])
                        })
                        $.users[v.api].ws.on('f',function (d){
                            $.ccio.globalWebsocket(d,$.users[v.api])
                        })
                    }
                })
            })
        }
    })
})
PNotify.prototype.options.styling = "fontawesome";
$user.ws.on('ping', function(d){
    $user.ws.emit('pong',{beat:1});
});
$user.ws.on('f',function (d){
    $.ccio.globalWebsocket(d)
    switch(d.f){
        case'api_key_deleted':
            $.ccio.init('note',{title:'<%-cleanLang(lang['API Key Deleted'])%>',text:'<%-cleanLang(lang.APIKeyDeletedText)%>',type:'notice'});
            $('[api_key="'+d.form.code+'"]').remove();
        break;
        case'api_key_added':
            $.ccio.init('note',{title:'<%-cleanLang(lang['API Key Added'])%>',text:'<%-cleanLang(lang.FiltersUpdatedText)%>',type:'success'});
            $.ccio.tm(3,d.form,'#api_list')
        break;
        case'filters_change':
            $.ccio.init('note',{title:'<%-cleanLang(lang['Filters Updated'])%>',text:'<%-cleanLang(lang.FiltersUpdatedText)%>',type:'success'});
            $user.details.filters=d.filters;
            $.ccio.init('filters');
        break;
        case'user_settings_change':
            $.ccio.init('note',{title:'<%-cleanLang(lang['Settings Changed'])%>',text:'<%-cleanLang(lang.SettingsChangedText)%>',type:'success'});
            $.ccio.init('id',d.form);
            d.form.details=JSON.parse(d.form.details)
            $('#custom_css').append(d.form.details.css)
            if(d.form.details){
                $user.details=d.form.details
            }
        break;
        case'users_online':
            $.ccio.pm('user-row',d.users);
        break;
        case'user_status_change':
            if(d.status===1){
                $.ccio.tm('user-row',d.user,null)
            }else{
                $('.user-row[uid="'+d.uid+'"][ke="'+d.ke+'"]').remove()
            }
        break;
        case'ffprobe_stop':
            $.pB.e.find('._loading').hide()
            $.pB.o.append('<div><b>END</b></div>');
            $.pB.e.find('.stop').hide();
            $.pB.e.find('[type="submit"]').show();
        break;
        case'ffprobe_start':
            $.pB.e.find('._loading').show()
            $.pB.o.empty();
            $.pB.e.find('.stop').show();
            $.pB.e.find('[type="submit"]').hide();
        break;
        case'ffprobe_data':
            $.pB.results=JSON.parse(d.data)
            $.pB.o.append($.ccio.init('jsontoblock',$.pB.results))
        break;
        case'detector_cascade_list':
            d.tmp=''
            $.each(d.cascades,function(n,v){
                d.tmp+='<li class="mdl-list__item">';
                d.tmp+='<span class="mdl-list__item-primary-content">';
                d.tmp+=v;
                d.tmp+='</span>';
                d.tmp+='<span class="mdl-list__item-secondary-action">';
                d.tmp+='<label class="mdl-switch mdl-js-switch mdl-js-ripple-effect">';
                d.tmp+='<input type="checkbox" value="'+v+'" detailContainer="detector_cascades" detailObject="'+v+'" class="detector_cascade_selection mdl-switch__input"/>';
                d.tmp+='</label>';
                d.tmp+='</span>';
                d.tmp+='</li>';
            })
            $('#detector_cascade_list').html(d.tmp)
            componentHandler.upgradeAllRegistered()
            //add auto select for preferences
            d.currentlyEditing=$.aM.e.attr('mid')
            if(d.currentlyEditing&&d.currentlyEditing!==''){
                d.currentlyEditing=JSON.parse(JSON.parse($.ccio.mon[d.currentlyEditing].details).detector_cascades)
                console.log(d.currentlyEditing)
                $.each(d.currentlyEditing,function(m,b){
                    d.e=$('.detector_cascade_selection[value="'+m+'"]').prop('checked',true)
                    d.p=d.e.parents('.mdl-js-switch')
                    if(d.p.length>0){
                        d.p.addClass('is-checked')
                    }
                })
            }
        break;
        case'detector_plugged':
            if(!d.notice){d.notice=''}
            $('.shinobi-detector').show()
            $('.shinobi-detector-msg').html(d.notice)
            $('.shinobi-detector_name').text(d.plug)
            $('.shinobi-detector-'+d.plug).show()
            $('.shinobi-detector-invert').hide()
            $.aM.drawList()
        break;
        case'detector_unplugged':
            $('.stream-objects .stream-detected-object').remove()
            $('.shinobi-detector').hide()
            $('.shinobi-detector-msg').empty()
            $('.shinobi-detector_name').empty()
            $('.shinobi-detector_plug').hide()
            $('.shinobi-detector-invert').show()
            $.aM.drawList()
        break;
        case'monitor_edit_failed':
            d.pnote={title:'Monitor Not Saved',text:'<b>'+d.mon.name+'</b> <small>'+d.mon.mid+'</small> has not been saved.',type:'error'}
            switch(d.ff){
                case'max_reached':
                    d.pnote.text+=' <%-cleanLang(lang.monitorEditFailedMaxReached)%>'
                break;
            }
            $.ccio.init('note',d.pnote);
        break;
//        case'onvif_end':
//            if(Object.keys($.oB.foundMonitorsCount).length===0){
//                $.oB.e.find('._loading').hide()
//                $.oB.e.find('[type="submit"]').prop('disabled',false)
//                $.oB.o.append('<td class="text-center _notfound">Sorry, nothing was found.</td>')
//            }
//        break;
        case'onvif':
            var tempID = $.ccio.gid();
            $.oB.foundMonitors[tempID] = Object.assign({},d);
            $.oB.e.find('._loading').hide()
            $.oB.e.find('._notfound').remove()
            $.oB.e.find('[type="submit"]').prop('disabled',false)
            d.info=$.ccio.init('jsontoblock',d.info)
            if(d.url){
                d.stream=d.url.uri
                d.info+=$.ccio.init('jsontoblock',d.url)
            }else{
                d.stream='URL not Found'
            }
            $('#onvif_probe .output_data').append('<tr onvif_row="'+tempID+'"><td><a class="btn btn-sm btn-primary copy">&nbsp;<i class="fa fa-copy"></i>&nbsp;</a></td><td class="ip">'+d.ip+'</td><td class="port">'+d.port+'</td><td>'+$.ccio.init('jsontoblock',d.info)+'</td><td class="url">'+d.stream+'</td><td class="date">'+d.date+'</td></tr>')
        break;
    }
    delete(d);
});
$.ccio.cx=function(x,user){
    if(!user){user=$user}
    if(!x.ke){x.ke=user.ke;};
    if(!x.uid){x.uid=user.uid;};
    return user.ws.emit('f',x)
}

$(document).ready(function(e){
console.log("%cWarning!", "font: 2em monospace; color: red;");
console.log('%cLeaving the developer console open is fine if you turn off "Network Recording". This is because it will keep a log of all files, including frames and videos segments.', "font: 1.2em monospace; ");
//global form functions
$.ccio.form={};
$.ccio.form.details=function(e){
    e.ar={},e.f=$(this).parents('form');
    $.each(e.f.find('[detail]'),function(n,v){
        v=$(v);e.ar[v.attr('detail')]=v.val();
    });
    e.f.find('[name="details"]').val(JSON.stringify(e.ar));
};
//onvif probe
$.oB={
    e:$('#onvif_probe'),
    v:$('#onvif_video'),
};
$.oB.f=$.oB.e.find('form');$.oB.o=$.oB.e.find('.output_data');
$.oB.f.submit(function(ee){
    ee.preventDefault();
    e={};
    $.oB.foundMonitors={}
    e.e=$(this),e.s=e.e.serializeObject();
    $.oB.o.empty();
    $.oB.e.find('._loading').show()
    $.oB.e.find('[type="submit"]').prop('disabled',true)
    $.ccio.cx({f:'onvif',ip:e.s.ip,port:e.s.port,user:e.s.user,pass:e.s.pass})
    clearTimeout($.oB.checkTimeout)
    $.oB.checkTimeout=setTimeout(function(){
        if($.oB.o.find('tr').length===0){
            $.oB.e.find('._loading').hide()
            $.oB.e.find('[type="submit"]').prop('disabled',false)
            $.oB.o.append('<td class="text-center _notfound">Sorry, nothing was found.</td>')
        }
    },5000)
    return false;
});
$.oB.e.on('click','.copy',function(){
    $('.hidden-xs [monitor="edit"]').click();
    e={};
    e.e = $(this).parents('[onvif_row]');
    var id = e.e.attr('onvif_row');
    var onvifRecord = $.oB.foundMonitors[id];
    console.log(onvifRecord)
    var streamURL = onvifRecord.url.uri;
    if($.oB.e.find('[name="user"]').val()!==''){
        streamURL = streamURL.split('://')
        streamURL = streamURL[0]+'://'+$.oB.e.find('[name="user"]').val()+':'+$.oB.e.find('[name="pass"]').val()+'@'+streamURL[1];
    }
    $.aM.e.find('[detail="auto_host"]').val(streamURL).change()
    $.aM.e.find('[name="mode"]').val('start')
    $.oB.e.modal('hide')
})
$.oB.e.find('[name="ip"]').change(function(e){
    $.ccio.op('onvif_probe_ip',$(this).val());
})
if($.ccio.op().onvif_probe_ip){
    $.oB.e.find('[name="ip"]').val($.ccio.op().onvif_probe_ip)
}
$.oB.e.find('[name="port"]').change(function(e){
    $.ccio.op('onvif_probe_port',$(this).val());
})
if($.ccio.op().onvif_probe_port){
    $.oB.e.find('[name="port"]').val($.ccio.op().onvif_probe_port)
}
$.oB.e.find('[name="user"]').change(function(e){
    $.ccio.op('onvif_probe_user',$(this).val());
})
if($.ccio.op().onvif_probe_user){
    $.oB.e.find('[name="user"]').val($.ccio.op().onvif_probe_user)
}
//Group Selector
$.gR={e:$('#group_list'),b:$('#group_list_button')};
$.gR.drawList=function(){
  var e={};
    e.tmp='';
    $.each($.ccio.init('monGroup'),function(n,v){
        if($user.mon_groups[n]){
           e.tmp+='<li class="mdl-menu__item" group="'+n+'">'+$user.mon_groups[n].name+'</li>'
        }
    })
    $.gR.e.html(e.tmp)
}
$.gR.e.on('click','[groups]',function(){
  var e={};
    e.e=$(this),
    e.a=e.e.attr('groups');
    var user=$.users[e.e.attr('auth')];
    if(!user){user=$user}
    if(user===$user){
        e.chosen_set='watch_on'
    }else{
        e.chosen_set='watch_on_links'
    }
    $.each($.ccio.op()[e.chosen_set],function(n,v){
        $.each(v,function(m,b){
            $.ccio.cx({f:'monitor',ff:'watch_off',id:m,ke:n},user)
        })
    })
    $.each($.ccio.mon_groups[e.a],function(n,v){
        $.ccio.cx({f:'monitor',ff:'watch_on',id:v.mid,ke:v.ke},user)
    })
})
//Region Editor
$.zO={e:$('#region_editor')};
$.zO.f=$.zO.e.find('form');
$.zO.o=function(){return $.zO.e.find('canvas')};
$.zO.c=$.zO.e.find('.canvas_holder');
$.zO.name=$.zO.e.find('[name="name"]');
$.zO.rl=$('#regions_list');
$.zO.rp=$('#regions_points');
$.zO.ca=$('#regions_canvas');
$.zO.saveCoords=function(){
    $.aM.e.find('[detail="cords"]').val(JSON.stringify($.zO.regionViewerDetails.cords)).change()
}
$.zO.initRegionList=function(){
    $('#regions_list,#region_points').empty();
    $.each($.zO.regionViewerDetails.cords,function(n,v){
        if(v&&v.name){
            $.zO.rl.append('<option value="'+n+'">'+v.name+'</option>')
        }
    });
    $.zO.rl.change();
}
$.zO.rl.change(function(e){
    $.zO.initCanvas();
})
$.zO.initLiveStream=function(e){
  var e={}
    e.re=$('#region_editor_live');
    e.re.find('iframe,img').attr('src','about:blank').hide()
    if($('#region_still_image').is(':checked')){
        e.re=e.re.find('img')
        e.choice='jpeg'
    }else{
        e.re=e.re.find('iframe')
        e.choice='embed'
    }
    e.src='/'+$user.auth_token+'/'+e.choice+'/'+$user.ke+'/'+$.aM.selected.mid
    if(e.choice=='embed'){
        e.src+='/fullscreen|jquery|relative'
    }else{
         e.src+='/s.jpg'
    }
    if(e.re.attr('src')!==e.src){
        e.re.attr('src',e.src).show()
    }
    e.re.attr('width',$.zO.regionViewerDetails.detector_scale_x)
    e.re.attr('height',$.zO.regionViewerDetails.detector_scale_y)
}
$('#region_still_image').change(function(e){
    e.o=$.ccio.op().switches
    if(!e.o){e.o={}}
    if($(this).is(':checked')){
        e.o.regionStillImage=1
    }else{
        e.o.regionStillImage="0"
    }
    $.ccio.op('switches',e.o)
    $.zO.initLiveStream()
}).ready(function(e){
    e.switches=$.ccio.op().switches
    if(e.switches&&e.switches.regionStillImage===1){
        $('#region_still_image').prop('checked',true)
    }
})
$.zO.initCanvas=function(){
  var e={};
    e.ar=[];
    e.val=$.zO.rl.val();
    if(!e.val){
        $.zO.f.find('[name="name"]').val('')
        $.zO.f.find('[name="sensitivity"]').val('')
        $.zO.rp.empty()
    }else{
        e.cord=$.zO.regionViewerDetails.cords[e.val];
        if(!e.cord.points){e.cord.points=[[0,0],[0,100],[100,0]]}
        $.each(e.cord.points,function(n,v){
            e.ar=e.ar.concat(v)
        });
        if(isNaN(e.cord.sensitivity)){
            e.cord.sensitivity=$.zO.regionViewerDetails.detector_sensitivity;
        }
        $.zO.f.find('[name="name"]').val(e.val)
        $.zO.e.find('.cord_name').text(e.val)
        $.zO.f.find('[name="sensitivity"]').val(e.cord.sensitivity)
        $.zO.e.find('.canvas_holder canvas').remove();
        
        $.zO.initLiveStream()
        e.e=$.zO.ca.val(e.ar.join(','))
        e.e.canvasAreaDraw({
            imageUrl:placeholder.getData(placeholder.plcimg({
                bgcolor:'transparent',
                text:' ',
                size:$.zO.regionViewerDetails.detector_scale_x+'x'+$.zO.regionViewerDetails.detector_scale_y
            }))
        });
        e.e.change();
    }
}
$.zO.e.on('change','[name="sensitivity"]',function(e){
    e.val=$(this).val();
    $.zO.regionViewerDetails.cords[$.zO.rl.val()].sensitivity=e.val;
    $.zO.saveCoords()
})
$.zO.e.on('change','[name="name"]',function(e){
    e.old=$.zO.rl.val();
    e.new=$.zO.name.val();
    $.zO.regionViewerDetails.cords[e.new]=$.zO.regionViewerDetails.cords[e.old];
    delete($.zO.regionViewerDetails.cords[e.old]);
    $.zO.rl.find('option[value="'+e.old+'"]').attr('value',e.new).text(e.new)
    $.zO.saveCoords()
})
$.zO.e.on('change','[point]',function(e){
    e.points=[];
    $('[points]').each(function(n,v){
        v=$(v);
        n=v.find('[point="x"]').val();
        if(n){
            e.points.push([n,v.find('[point="y"]').val()])
        }
    })
    $.zO.regionViewerDetails.cords[$.zO.name.val()].points=e.points;
    $.zO.initCanvas();
})
$.zO.e.find('.erase').click(function(e){
    e.arr=[]
    $.each($.zO.regionViewerDetails.cords,function(n,v){
        if(v&&v!==$.zO.regionViewerDetails.cords[$.zO.rl.val()]){
            e.arr.push(v)
        }
    })
    $.zO.regionViewerDetails.cords=e.arr.concat([]);
    if(Object.keys($.zO.regionViewerDetails.cords).length>0){
        $.zO.initRegionList();
    }else{
        $.zO.f.find('input').prop('disabled',true)
        $('#regions_points tbody').empty()
        $('#regions_list [value="'+$.zO.rl.val()+'"]').remove()
        $.aM.e.find('[detail="cords"]').val('[]')
    }
});
//$.zO.e.find('.new').click(function(e){
//    $.zO.regionViewerDetails.cords[$.zO.rl.val()]
//    $.zO.initRegionList();
//})
$.zO.e.on('changed','#regions_canvas',function(e){
    e.val=$(this).val().replace(/(,[^,]*),/g, '$1;').split(';');
    e.ar=[];
    $.each(e.val,function(n,v){
        v=v.split(',')
        if(v[1]){
            e.ar.push([v[0],v[1]])
        }
    })
    $.zO.regionViewerDetails.cords[$.zO.rl.val()].points=e.ar;
    e.selected=$.zO.regionViewerDetails.cords[$.zO.rl.val()];
    e.e=$('#regions_points tbody').empty();
    $.each($.zO.regionViewerDetails.cords[$.zO.rl.val()].points,function(n,v){
        if(isNaN(v[0])){v[0]=20}
        if(isNaN(v[1])){v[1]=20}
        e.e.append('<tr points="'+n+'"><td><input class="form-control" placeholder="X" point="x" value="'+v[0]+'"></td><td><input class="form-control" placeholder="Y" point="y" value="'+v[1]+'"></td><td class="text-right"><a class="delete btn btn-danger"><i class="fa fa-trash-o"></i></a></td></tr>')
    });
    $.zO.saveCoords()
})
$.zO.f.submit(function(e){
    e.preventDefault();e.e=$(this),e.s=e.e.serializeObject();
    
    return false;
});
$('#regions_points')
.on('click','.delete',function(e){
    e.p=$(this).parents('tr'),e.row=e.p.attr('points');
    delete($.zO.regionViewerDetails.cords[$.zO.rl.val()].points[e.row])
    $.zO.saveCoords()
    e.p.remove();
    $.zO.rl.change();
})
$.zO.e.on('click','.add',function(e){
    $.zO.f.find('input').prop('disabled',false)
    e.gid=$.ccio.gid(5);
    e.save={};
    $.each($.zO.regionViewerDetails.cords,function(n,v){
        if(v&&v!==null&&v!=='null'){
            e.save[n]=v;
        }
    })
    $.zO.regionViewerDetails.cords=e.save;
    $.zO.regionViewerDetails.cords[e.gid]={name:e.gid,sensitivity:0.0005,points:[[0,0],[0,100],[100,0]]};
    $.zO.rl.append('<option value="'+e.gid+'">'+e.gid+'</option>');
    $.zO.rl.val(e.gid)
    $.zO.rl.change();
});
//probe
$.pB={e:$('#probe')};$.pB.f=$.pB.e.find('form');$.pB.o=$.pB.e.find('.output_data');
$.pB.f.submit(function(e){

    $.pB.e.find('._loading').show()
    $.pB.o.empty();
    $.pB.e.find('.stop').show();
    $.pB.e.find('[type="submit"]').hide();
    
    e.preventDefault();e.e=$(this),e.s=e.e.serializeObject();
    e.s.url=e.s.url.trim();
    var flags = '';
    switch(e.s.mode){
        case'json':
            flags = '-v quiet -print_format json -show_format -show_streams';
        break;
    }
//    if(e.s.url.indexOf('{{JSON}}')>-1){
//        e.s.url='-v quiet -print_format json -show_format -show_streams '+e.s.url
//    }
    $.get('/'+$user.auth_token+'/probe/'+$user.ke+'?url='+e.s.url+'&flags='+flags,function(data){
        if(data.ok===true){
            var html
            try{
                html = $.ccio.init('jsontoblock',JSON.parse(data.result))
            }catch(err){
                html = data.result
            }
            $.pB.o.append(html)
        }else{
            $.ccio.init('note',{title:'Failed to Probe',text:data.error,type:'error'});
        }
        $.pB.e.find('._loading').hide()
        $.pB.o.append('<div><b>END</b></div>');
        $.pB.e.find('.stop').hide();
        $.pB.e.find('[type="submit"]').show();
    })
    return false;
});
$.pB.e.on('hidden.bs.modal',function(){
    $.pB.o.empty()
})
$.pB.e.find('.stop').click(function(e){
    e.e=$(this);
//    $.ccio.cx({f:'ffprobe',ff:'stop'})
});
//log viewer
$.log={e:$('#logs_modal'),lm:$('#log_monitors')};$.log.o=$.log.e.find('table tbody');
$.log.e.on('shown.bs.modal', function () {
    $.log.lm.find('option:not(.hard)').remove()
    $.each($.ccio.mon,function(n,v){
        v.id=v.mid;
        $.ccio.tm('option',v,'#log_monitors')
    })
    $.log.lm.change()
});
$.log.lm.change(function(e){
    e.v=$(this).val();
    if(e.v==='all'){e.v=''}
    $.get('/'+$user.auth_token+'/logs/'+$user.ke+'/'+e.v,function(d){
        e.tmp='';
        $.each(d,function(n,v){
            e.tmp+='<tr class="search-row"><td title="'+v.time+'" class="livestamp"></td><td>'+v.time+'</td><td>'+v.name+'</td><td>'+v.mid+'</td><td>'+$.ccio.init('jsontoblock',v.info)+'</td></tr>'
        })
        $.log.o.html(e.tmp)
        $.ccio.init('ls')
    })
});
//multi monitor manager
$.multimon={e:$('#multi_mon')};
$.multimon.table=$.multimon.e.find('.tableData tbody');
$.multimon.f=$.multimon.e.find('form');
$.multimon.f.on('change','#multimon_select_all',function(e){
    e.e=$(this);
    e.p=e.e.prop('checked')
    e.a=$.multimon.f.find('input[type=checkbox][name]')
    if(e.p===true){
        e.a.prop('checked',true)
    }else{
        e.a.prop('checked',false)
    }
})
$.multimon.e.find('.import_config').click(function(){
  var e={};e.e=$(this);e.mid=e.e.parents('[mid]').attr('mid');
    $.confirm.e.modal('show');
    $.confirm.title.text('<%-cleanLang(lang['Import Monitor Configuration'])%>')
    e.html='<%-cleanLang(lang.ImportMultiMonitorConfigurationText)%><div style="margin-top:15px"><div class="form-group"><textarea placeholder="<%-cleanLang(lang['Paste JSON here.'])%>" class="form-control"></textarea></div><label class="upload_file btn btn-primary btn-block"> Upload File <input class="upload" type=file name="files[]"></label></div>';
    $.confirm.body.html(e.html)
    $.confirm.e.find('.upload').change(function(e){
        var files = e.target.files; // FileList object
        f = files[0];
        var reader = new FileReader();
        reader.onload = function(ee) {
            $.confirm.e.find('textarea').val(ee.target.result);
        }
        reader.readAsText(f);
    });
    $.confirm.click({title:'Import',class:'btn-primary'},function(){
//        setTimeout(function(){
//            $.confirm.e.modal('show');
//        },1000)
//        $.confirm.title.text('<%-cleanLang(lang['Are you sure?'])%>')
//        $.confirm.body.html('<%-cleanLang(lang.ImportMultiMonitorConfigurationText)%>')
//        $.confirm.click({title:'Save Set',class:'btn-danger'},function(){
            try{
                var postMonitor = function(v){
                    $.post('/'+$user.auth_token+'/configureMonitor/'+$user.ke+'/'+v.mid,{data:JSON.stringify(v,null,3)},function(d){
                        $.ccio.log(d)
                    })
                }
                e.monitorList=JSON.parse($.confirm.e.find('textarea').val());
                if(e.monitorList.mid){
                    postMonitor(e.monitorList)
                }else{
                    $.each(e.monitorList,function(n,v){
                        postMonitor(v)
                    })
                }
            }catch(err){
                $.ccio.log(err)
                $.ccio.init('note',{title:'<%-cleanLang(lang['Invalid JSON'])%>',text:'<%-cleanLang(lang.InvalidJSONText)%>',type:'error'})
            }
//        });
    });
})
$.multimon.getSelectedMonitors = function(){
    var arr=[];
    var monitors = $.ccio.init('cleanMons','object')
    $.each($.multimon.f.serializeObject(),function(n,v){
        arr.push(monitors[n])
    })
    return arr;
}
$.multimon.e.find('.delete').click(function(){
    var arr=$.multimon.getSelectedMonitors();
    if(arr.length===0){
        $.ccio.init('note',{title:'No Monitors Selected',text:'Select atleast one monitor to delete.',type:'error'});
        return
    }
    $.confirm.e.modal('show');
    $.confirm.title.text('<%-cleanLang(lang['Delete'])%> <%-cleanLang(lang['Monitors'])%>')
    e.html='<p><%-cleanLang(lang.DeleteMonitorsText)%></p>';
    $.confirm.body.html(e.html)
    $.confirm.click({title:'Delete',class:'btn-danger'},function(){
        $.each(arr,function(n,v){
            $.get('/'+v.user.auth_token+'/configureMonitor/'+v.ke+'/'+v.mid+'/delete',function(data){
                console.log(data)
            })
        })
    });
})
//$.multimon.e.find('.edit_all').click(function(){
//    var arr=$.multimon.getSelectedMonitors();
//    var arrObject={}
//    if(arr.length===0){
//        $.ccio.init('note',{title:'No Monitors Selected',text:'Select atleast one monitor to delete.',type:'error'});
//        return
//    }
//    $.multimonedit.selectedList = arr;
//    $.multimonedit.e.modal('show')
//})
$.multimon.e.find('.save_config').click(function(){
    var e={};e.e=$(this);
    var arr=$.multimon.getSelectedMonitors();
    if(arr.length===0){
        $.ccio.init('note',{title:'No Monitors Selected',text:'Select atleast one monitor to delete.',type:'error'});
        return
    }
    e.dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(arr));
    $('#temp').html('<a></a>')
        .find('a')
        .attr('href',e.dataStr)
        .attr('download','Shinobi_Monitors_'+(new Date())+'.json')
        [0].click()
})
$.multimon.e.on('shown.bs.modal',function() {
    var tmp=''
    $.each($.ccio.mon,function(n,v){
        var streamURL = $.ccio.init('streamURL',v)
        if(streamURL!=='Websocket'&&v.mode!==('idle'&&'stop')){
            streamURL='<a target="_blank" href="'+streamURL+'">'+streamURL+'</a>'
        }
        var img = $('#left_menu [mid="'+v.mid+'"][auth="'+v.user.auth_token+'"] [monitor="watch"]').attr('src')
        tmp+='<tr mid="'+v.mid+'" ke="'+v.ke+'" auth="'+v.user.auth_token+'">'
        tmp+='<td><div class="checkbox"><input id="multimonCheck_'+v.ke+v.mid+v.user.auth_token+'" type="checkbox" name="'+v.ke+v.mid+v.user.auth_token+'" value="1"><label for="multimonCheck_'+v.ke+v.mid+v.user.auth_token+'"></label></div></td>'
        tmp+='<td><a monitor="watch"><img class="small-square-img" src="'+img+'"></a></td><td>'+v.name+'<br><small>'+v.mid+'</small></td><td class="monitor_mode">'+$.ccio.init('humanReadMode',v.mode)+'</td><td>'+streamURL+'</td>'
        //buttons
        tmp+='<td class="text-right"><a title="<%-cleanLang(lang.Pop)%>" monitor="pop" class="btn btn-primary"><i class="fa fa-external-link"></i></a> <a title="<%-cleanLang(lang.Calendar)%>" monitor="calendar" class="btn btn-default"><i class="fa fa-calendar"></i></a> <a title="<%-cleanLang(lang['Power Viewer'])%>" class="btn btn-default" monitor="powerview"><i class="fa fa-map-marker"></i></a> <a title="<%-cleanLang(lang['Time-lapse'])%>" class="btn btn-default" monitor="timelapse"><i class="fa fa-angle-double-right"></i></a> <a title="<%-cleanLang(lang['Videos List'])%>" monitor="videos_table" class="btn btn-default"><i class="fa fa-film"></i></a> <a title="<%-cleanLang(lang['Monitor Settings'])%>" class="btn btn-default permission_monitor_edit" monitor="edit"><i class="fa fa-wrench"></i></a></td>'
        tmp+='</tr>'
    })
    $.multimon.table.html(tmp)
})
//Monitor Editor
$.aM={e:$('#add_monitor'),monitorsForCopy:$('#copy_settings_monitors')};
$.aM.f=$.aM.e.find('form')
$.aM.channels=$('#monSectionStreamChannels')
$.aM.maps=$('#monSectionInputMaps')
$.aM.e.find('.follow-list ul').affix();
$.each(<%-JSON.stringify(define["Monitor Settings"].blocks)%>,function(n,v){
    $.each(v.info,function(m,b){
        if(!b.name){
            console.log(b)
            return
        }
        if(b.name.indexOf('detail=')>-1){
            b.name=b.name.replace('detail=','')
            v.element=$('[detail="'+b.name+'"]')
        }else{
            v.element=$('[name="'+b.name+'"]')
        }
        v.parent=v.element.parents('.form-group').find('label div:first-child span')
        v.parent.find('small').remove()
        v.parent.append('<small class="hover">'+b.description+'</small>')
    })
})
$.aM.generateDefaultMonitorSettings=function(){
    return {
    "mode": "start",
    "mid": $.ccio.gid(),
    "name": "Some Stream",
    "type": "h264",
    "protocol": "rtsp",
    "host": "",
    "port": "",
    "path": "",
    "ext": "mp4",
    "fps": "1",
    "width": "640",
    "height": "480",
    "details": JSON.stringify({
        "fatal_max": "0",
        "notes": "",
        "dir": "",
        "auto_host_enable": "1",
        "auto_host": "",
        "rtsp_transport": "tcp",
        "muser": "",
        "mpass": "",
        "port_force": "0",
        "aduration": "1000000",
        "probesize": "1000000",
        "stream_loop": "0",
        "sfps": "1",
        "accelerator": "1",
        "hwaccel": "auto",
        "hwaccel_vcodec": "",
        "hwaccel_device": "",
        "stream_type": "mp4",
        "stream_flv_type": "ws",
        "stream_mjpeg_clients": "",
        "stream_vcodec": "copy",
        "stream_acodec": "no",
        "hls_time": "2",
        "preset_stream": "ultrafast",
        "hls_list_size": "3",
        "signal_check": "10",
        "signal_check_log": "0",
        "stream_quality": "15",
        "stream_fps": "2",
        "stream_scale_x": "",
        "stream_scale_y": "",
        "rotate_stream": "no",
        "svf": "",
        "rtmp_vcodec": "h264",
        "rtmp_acodec": "aac",
        "stream_timestamp": "0",
        "stream_timestamp_font": "",
        "stream_timestamp_font_size": "",
        "stream_timestamp_color": "",
        "stream_timestamp_box_color": "",
        "stream_timestamp_x": "",
        "stream_timestamp_y": "",
        "stream_watermark": "0",
        "stream_watermark_location": "",
        "stream_watermark_position": "tr",
        "snap": "1",
        "snap_fps": "",
        "snap_scale_x": "",
        "snap_scale_y": "",
        "snap_vf": "",
        "rawh264": "0",
        "rawh264_vcodec": "copy",
        "rawh264_acodec": "",
        "rawh264_fps": "",
        "rawh264_scale_x": "",
        "rawh264_scale_y": "",
        "rawh264_crf": "",
        "rawh264_vf": "",
        "vcodec": "copy",
        "crf": "1",
        "preset_record": "",
        "acodec": "no",
        "dqf": "0",
        "cutoff": "15",
        "rotate_record": "no",
        "vf": "",
        "timestamp": "0",
        "timestamp_font": "",
        "timestamp_font_size": "10",
        "timestamp_color": "white",
        "timestamp_box_color": "0x00000000@1",
        "timestamp_x": "(w-tw)/2",
        "timestamp_y": "0",
        "watermark": "0",
        "watermark_location": "",
        "watermark_position": "tr",
        "cust_input": "",
        "cust_snap": "",
        "cust_rawh264": "",
        "cust_detect": "",
        "cust_stream": "",
        "cust_stream_server": "",
        "cust_record": "",
        "custom_output": "",
        "detector": "0",
        "detector_pam": "1",
        "detector_webhook": "0",
        "detector_webhook_url": "",
        "detector_command_enable": "0",
        "detector_command": "",
        "detector_command_timeout": "",
        "detector_lock_timeout": "",
        "detector_save": "0",
        "detector_frame_save": "0",
        "detector_mail": "0",
        "detector_mail_timeout": "",
        "detector_record_method": "sip",
        "detector_trigger": "1",
        "detector_trigger_record_fps": "",
        "detector_timeout": "10",
        "watchdog_reset": "0",
        "detector_delete_motionless_videos": "0",
        "detector_send_frames": "1",
        "detector_region_of_interest": "0",
        "detector_fps": "",
        "detector_scale_x": "640",
        "detector_scale_y": "480",
        "detector_use_motion": "1",
        "detector_use_detect_object": "0",
        "detector_frame": "0",
        "detector_sensitivity": "",
        "cords": "[]",
        "detector_buffer_vcodec": "auto",
        "detector_buffer_fps": "",
        "detector_buffer_hls_time": "",
        "detector_buffer_hls_list_size": "",
        "detector_buffer_start_number": "",
        "detector_buffer_live_start_index": "",
        "detector_lisence_plate": "0",
        "detector_lisence_plate_country": "us",
        "detector_notrigger": "0",
        "detector_notrigger_mail": "0",
        "detector_notrigger_timeout": "",
        "control": "0",
        "control_base_url": "",
        "control_stop": "0",
        "control_url_stop_timeout": "",
        "control_url_center": "",
        "control_url_left": "",
        "control_url_left_stop": "",
        "control_url_right": "",
        "control_url_right_stop": "",
        "control_url_up": "",
        "control_url_up_stop": "",
        "control_url_down": "",
        "control_url_down_stop": "",
        "control_url_enable_nv": "",
        "control_url_disable_nv": "",
        "control_url_zoom_out": "",
        "control_url_zoom_out_stop": "",
        "control_url_zoom_in": "",
        "control_url_zoom_in_stop": "",
        "tv_channel": "0",
        "groups": "[]",
        "loglevel": "warning",
        "sqllog": "0",
        "detector_cascades": ""
    }),
    "shto": "[]",
    "shfr": "[]"
}
}
$.aM.drawList=function(){
    e={list:$.aM.e.find('.follow-list ul'),html:''}
    $.aM.e.find('[section]:visible').each(function(n,v){
        e.e=$(v)
        e.id = e.e.attr('id');
        e.title = e.e.find('h4').first().html();
        var div = document.createElement('div');
        div.innerHTML = e.title;
        var elements = div.getElementsByTagName('a');
        while (elements[0])
           elements[0].parentNode.removeChild(elements[0])
        var elements = div.getElementsByTagName('small');
        while (elements[0])
           elements[0].parentNode.removeChild(elements[0])
        var repl = div.innerHTML;
        e.html += '<li><a class="scrollTo" href="#'+e.id+'" scrollToParent="#add_monitor .modal-body">'+repl+'</a></li>'
    })
    e.list.html(e.html)
}
$.aM.import=function(e){
    $('#monEditBufferPreview').attr('src','/'+$user.auth_token+'/hls/'+e.values.ke+'/'+e.values.mid+'/detectorStream.m3u8')
    $.aM.e.find('.edit_id').text(e.values.mid);
    $.aM.e.attr('mid',e.values.mid).attr('ke',e.values.ke).attr('auth',e.auth)
    $.each(e.values,function(n,v){
        $.aM.e.find('[name="'+n+'"]').val(v).change()
    })
    e.ss=JSON.parse(e.values.details);
    //get maps
    $.aM.maps.empty()
    if(e.ss.input_maps&&e.ss.input_maps!==''){
        var input_maps
        try{
            input_maps = JSON.parse(e.ss.input_maps)
        }catch(er){
            input_maps = e.ss.input_maps;
        }
        var mapContainers = $('[input-mapping]')
        if(input_maps.length>0){
            mapContainers.show()
            $.each(input_maps,function(n,v){
                var tempID = $.ccio.tm('input-map')
                var parent = $('#monSectionMap'+tempID)
                $.each(v,function(m,b){
                    parent.find('[map-detail="'+m+'"]').val(b).change()
                })
            })
        }else{
            mapContainers.hide()
        }
    }
    //get channels
    $.aM.channels.empty()
    if(e.ss.stream_channels&&e.ss.stream_channels!==''){
        var stream_channels
        try{
            stream_channels = JSON.parse(e.ss.stream_channels)
        }catch(er){
            stream_channels = e.ss.stream_channels;
        }
        $.each(stream_channels,function(n,v){
            var tempID = $.ccio.tm('stream-channel')
            var parent = $('#monSectionChannel'+tempID)
            $.each(v,function(m,b){
                parent.find('[channel-detail="'+m+'"]').val(b)
            })
        })
    }
    //get map choices for outputs
    $('[input-mapping] .choices').empty()
    if(e.ss.input_map_choices&&e.ss.input_map_choices!==''){
        var input_map_choices
        try{
            input_map_choices = JSON.parse(e.ss.input_map_choices)
        }catch(er){
            input_map_choices = e.ss.input_map_choices;
        }
        $.each(input_map_choices,function(n,v){
            $.each(v,function(m,b){
                var parent = $('[input-mapping="'+n+'"] .choices')
                $.ccio.tm('input-map-selector',b,parent)
            })
        })
    }
    $.aM.e.find('[detail]').each(function(n,v){
        v=$(v).attr('detail');if(!e.ss[v]){e.ss[v]=''}
    })
    $.each(e.ss,function(n,v){
        var theVal = v;
        if(v instanceof Object){
            theVal = JSON.stringify(v);
        }
        $.aM.e.find('[detail="'+n+'"]').val(theVal).change();
    });
    $.each(e.ss,function(n,v){
        try{
            var variable=JSON.parse(v)
        }catch(err){
            var variable=v
        }
        if(variable instanceof Object){
            $('[detailContainer="'+n+'"][detailObject]').prop('checked',false)
            $('[detailContainer="'+n+'"][detailObject]').parents('.mdl-js-switch').removeClass('is-checked')
            if(variable instanceof Array){
                $.each(variable,function(m,b,parentOfObject){
                    $('[detailContainer="'+n+'"][detailObject="'+b+'"]').prop('checked',true)
                    parentOfObject=$('[detailContainer="'+n+'"][detailObject="'+b+'"]').parents('.mdl-js-switch')
                    parentOfObject.addClass('is-checked')
                })
            }else{
                $.each(variable,function(m,b){
                    if(typeof b ==='string'){
                       $('[detailContainer="'+n+'"][detailObject="'+m+'"]').val(b).change()
                    }else{
                        $('[detailContainer="'+n+'"][detailObject="'+m+'"]').prop('checked',true)
                        parentOfObject=$('[detailContainer="'+n+'"][detailObject="'+m+'"]').parents('.mdl-js-switch')
                        parentOfObject.addClass('is-checked')
                    }
                })
            }
        }
    });
    try{
        $.each(['groups','group_detector'],function(m,b){
            var tmp=''
            $.each($user.mon_groups,function(n,v){
                tmp+='<li class="mdl-list__item">';
                tmp+='<span class="mdl-list__item-primary-content">';
                tmp+=v.name;
                tmp+='</span>';
                tmp+='<span class="mdl-list__item-secondary-action">';
                tmp+='<label class="mdl-switch mdl-js-switch mdl-js-ripple-effect">';
                tmp+='<input type="checkbox" '+b+' value="'+v.id+'" class="mdl-switch__input"';
                if(!e.ss[b]){
                    e.ss[b]=[]
                }
                if(e.ss[b].indexOf(v.id)>-1){tmp+=' checked';}
                tmp+=' />';
                tmp+='</label>';
                tmp+='</span>';
                tmp+='</li>';
            })
            $('#monitor_'+b).html(tmp)
        })
        componentHandler.upgradeAllRegistered()
    }catch(er){
        console.log(er)
        //no group, this 'try' will be removed in future.
    };
    $('#copy_settings').val('0').change()
    var tmp = '';
    $.each($.ccio.mon,function(n,v){
        if(v.ke === $user.ke){
            tmp += $.ccio.tm('option',{auth_token:$user.auth_token,id:v.mid,name:v.name},null,$user);
        }
    })
    $.aM.monitorsForCopy.find('optgroup').html(tmp)
    setTimeout(function(){$.aM.drawList()},1000)
}
//parse "Automatic" field in "Input" Section
$.aM.e.on('change','[detail="auto_host"]',function(e){
    var isRTSP = false;
    var url = $(this).val()
    var theSwitch = $.aM.e.find('[detail="auto_host_enable"]')
    var disabled = theSwitch.val()
    if(!disabled||disabled===''){
        //if no value, then probably old version of monitor config. Set to Manual to avoid confusion.
        disabled='0'
        theSwitch.val('0').change()
    }
    if(disabled==='0'){
        return
    }
    var urlSplitByDots = url.split('.')
    var has = function(query,searchIn){if(!searchIn){searchIn=url;};return url.indexOf(query)>-1}
    //switch RTSP to parse URL
    if(has('rtsp://')){
        isRTSP = true;
        url = url.replace('rtsp://','http://')
    }
    //parse URL
    var parsedURL = document.createElement('a');
    parsedURL.href = url;
    if(isRTSP){
        $.aM.e.find('[name="protocol"]').val('rtsp').change()
        $.aM.e.find('[detail="rtsp_transport"]').val('tcp').change()
        $.aM.e.find('[detail="aduration"]').val(1000000).change()
        $.aM.e.find('[detail="probesize"]').val(1000000).change()
    }else{
        //not RTSP
        $.aM.e.find('[name="protocol"]').val(parsedURL.protocol.replace(/:/g,'').replace(/\//g,'')).change()
    }
    $.aM.e.find('[detail="muser"]').val(parsedURL.username).change()
    $.aM.e.find('[detail="mpass"]').val(parsedURL.password).change()
    $.aM.e.find('[name="host"]').val(parsedURL.hostname).change()
    $.aM.e.find('[name="port"]').val(parsedURL.port).change()
    $.aM.e.find('[name="path"]').val(parsedURL.pathname).change()
    delete(parsedURL)
})
$.aM.e.find('.refresh_cascades').click(function(e){
    $.ccio.cx({f:'ocv_in',data:{f:'refreshPlugins',ke:$user.ke}})
})
$.aM.f.submit(function(ee){
    ee.preventDefault();
    e={e:$(this)};
    e.s=e.e.serializeObject();
    e.er=[];
    $.each(e.s,function(n,v){e.s[n]=v.trim()});
    e.s.mid=e.s.mid.replace(/[^\w\s]/gi,'').replace(/ /g,'')
    if(e.s.mid.length<3){e.er.push('Monitor ID too short')}
    if(e.s.port==''){e.s.port=80}
    if(e.s.name==''){e.er.push('Monitor Name cannot be blank')}
//    if(e.s.protocol=='rtsp'){e.s.ext='mp4',e.s.type='rtsp'}
    if(e.er.length>0){
        $.sM.e.find('.msg').html(e.er.join('<br>'));
        $.ccio.init('note',{title:'Configuration Invalid',text:e.er.join('<br>'),type:'error'});
        return;
    }
    $.post('/'+$user.auth_token+'/configureMonitor/'+$user.ke+'/'+e.s.mid,{data:JSON.stringify(e.s)},function(d){
        $.ccio.log(d)
    })
    //
    if($('#copy_settings').val() === '1'){
        e.s.details = JSON.parse(e.s.details);
        var copyMonitors = $.aM.monitorsForCopy.val();
        var chosenSections = [];
        var chosenMonitors = {};
        
        if(!copyMonitors||copyMonitors.length===0){
            $.ccio.init('note',{title:'<%-cleanLang(lang['No Monitors Selected'])%>',text:'<%-cleanLang(lang.monSavedButNotCopied)%>'})
            return
        }
        
        $.aM.e.find('[copy]').each(function(n,v){
            var el = $(v)
            if(el.val() === '1'){
                chosenSections.push(el.attr('copy'))
            }
        })
        var alterSettings = function(settingsToAlter,monitor){
            monitor.details = JSON.parse(monitor.details);
            $.aM.e.find(settingsToAlter).find('input,select,textarea').each(function(n,v){
                var el = $(v);
                var name = el.attr('name')
                var detail = el.attr('detail')
                var value
                switch(true){
                    case !!name:
                        var value = e.s[name]
                        monitor[name] = value;
                    break;
                    case !!detail:
                        detail = detail.replace('"','')
                        var value = e.s.details[detail]
                        monitor.details[detail] = value;
                    break;
                }
            })
            monitor.details = JSON.stringify(monitor.details);
            return monitor;
        }
        $.each(copyMonitors,function(n,id){
            var monitor
            if(id === '$New'){
                monitor = $.aM.generateDefaultMonitorSettings();
                //connection
                monitor.name = e.s.name+' - '+monitor.mid
                monitor.type = e.s.type
                monitor.protocol = e.s.protocol
                monitor.host = e.s.host
                monitor.port = e.s.port
                monitor.path = e.s.path
                monitor.details.fatal_max = e.s.details.fatal_max
                monitor.details.port_force = e.s.details.port_force
                monitor.details.muser = e.s.details.muser
                monitor.details.password = e.s.details.password
                monitor.details.rtsp_transport = e.s.details.rtsp_transport
                monitor.details.auto_host = e.s.details.auto_host
                monitor.details.auto_host_enable = e.s.details.auto_host_enable
                //input
                monitor.details.aduration = e.s.details.aduration
                monitor.details.probesize = e.s.details.probesize
                monitor.details.stream_loop = e.s.details.stream_loop
                monitor.details.sfps = e.s.details.sfps
                monitor.details.accelerator = e.s.details.accelerator
                monitor.details.hwaccel = e.s.details.hwaccel
                monitor.details.hwaccel_vcodec = e.s.details.hwaccel_vcodec
                monitor.details.hwaccel_device = e.s.details.hwaccel_device
            }else{
                monitor = Object.assign({},$.ccio.init('cleanMon',$.ccio.mon[$user.ke+id+$user.auth_token]));
            }
            $.each(chosenSections,function(n,section){
                monitor = alterSettings(section,monitor)
            })
            console.log(monitor)
            $.post('/'+$user.auth_token+'/configureMonitor/'+$user.ke+'/'+monitor.mid,{data:JSON.stringify(monitor)},function(d){
                $.ccio.log(d)
            })
             chosenMonitors[monitor.mid] = monitor;
        })
        console.log(chosenMonitors)
    }
    
    $.aM.e.modal('hide')
    return false;
});
//////////////////
//Input Map (Feed)
$.aM.mapPlacementInit = function(){
    $('.input-map').each(function(n,v){
        var _this = $(this)
        _this.find('.place').text(n+1)
    })
}
$.aM.mapSave = function(){
    var e={};
    var mapContainers = $('[input-mapping]');
    var stringForSave={}
    mapContainers.each(function(q,t){
        var mapRowElement = $(t).find('.map-row');
        var mapRow = []
        mapRowElement.each(function(n,v){
            var map={}
            $.each($(v).find('[map-input]'),function(m,b){
                map[$(b).attr('map-input')]=$(b).val()
            });
            mapRow.push(map)
        });
        stringForSave[$(t).attr('input-mapping')] = mapRow;
    });
    $.aM.e.find('[detail="input_map_choices"]').val(JSON.stringify(stringForSave)).change();
}
$.aM.maps.on('click','.delete',function(){
    $(this).parents('.input-map').remove()
    var inputs = $('[map-detail]')
    var mapContainers = $('[input-mapping]');
    if(inputs.length===0){
        $.aM.e.find('[detail="input_maps"]').val('[]').change()
        mapContainers.hide();
    }else{
        inputs.first().change()
        mapContainers.show();
    }
    $.aM.mapPlacementInit()
})
$.aM.e.on('change','[map-detail]',function(){
  var e={};
    e.e=$.aM.maps.find('.input-map')
    e.s=[]
    e.e.each(function(n,v){
        var map={}
        $.each($(v).find('[map-detail]'),function(m,b){
            map[$(b).attr('map-detail')]=$(b).val()
        });
        e.s.push(map)
    });
    $.aM.e.find('[detail="input_maps"]').val(JSON.stringify(e.s)).change()
})
$.aM.e.on('click','[input-mapping] .add_map_row',function(){
    $.ccio.tm('input-map-selector',{},$(this).parents('[input-mapping]').find('.choices'))
    $.aM.mapSave()
})
$.aM.e.on('click','[input-mapping] .delete_map_row',function(){
    $(this).parents('.map-row').remove()
    $.aM.mapSave()
})
$.aM.e.on('change','[map-input]',function(){
    $.aM.mapSave()
})
//////////////////
//Stream Channels
$.aM.channelSave = function(){
  var e={};
    e.e=$.aM.channels.find('.stream-channel')
    e.s=[]
    e.e.each(function(n,v){
        var channel={}
        $.each($(v).find('[channel-detail]'),function(m,b){
            channel[$(b).attr('channel-detail')]=$(b).val()
        });
        e.s.push(channel)
    });
    $.aM.e.find('[detail="stream_channels"]').val(JSON.stringify(e.s)).change()
}
$.aM.channelPlacementInit = function(){
    $('.stream-channel').each(function(n,v){
        var _this = $(this)
        _this.attr('stream-channel',n)
        _this.find('.place').text(n)
        _this.find('[input-mapping]').attr('input-mapping','stream_channel-'+n)
        $.aM.mapSave()
    })
}
$.aM.channels.on('click','.delete',function(){
    $(this).parents('.stream-channel').remove()
    $.aM.channelSave()
    $.aM.channelPlacementInit()
})
$.aM.e.on('change','[channel-detail]',function(){
    $.aM.channelSave()
})
//////////////////
$.aM.e.on('change','[groups]',function(){
  var e={};
    e.e=$.aM.e.find('[groups]:checked');
    e.s=[];
    e.e.each(function(n,v){
        e.s.push($(v).val())
    });
    $.aM.e.find('[detail="groups"]').val(JSON.stringify(e.s)).change()
})
$.aM.e.on('change','.detector_cascade_selection',function(){
  var e={};
    e.e=$.aM.e.find('.detector_cascade_selection:checked');
    e.s={};
    e.e.each(function(n,v){
        e.s[$(v).val()]={}
    });
    $.aM.e.find('[detail="detector_cascades"]').val(JSON.stringify(e.s)).change()
})
//$.aM.e.on('change','.detector_cascade_selection',function(){
//  var e={};
//    e.details=$.aM.e.find('[name="details"]')
//    try{
//        e.detailsVal=JSON.parse(e.details.val())
//    }catch(err){
//        e.detailsVal={}
//    }
//    e.detailsVal.detector_cascades=[];
//    e.e=$.aM.e.find('.detector_cascade_selection:checked');
//    e.e.each(function(n,v){
//        e.detailsVal.detector_cascades.push($(v).val())
//    });
//    e.details.val(JSON.stringify(e.detailsVal))
//})
$.aM.e.find('.probe_config').click(function(){
  var e={};
    e.user=$.aM.e.find('[detail="muser"]').val();
    e.pass=$.aM.e.find('[detail="mpass"]').val();
    e.host=$.aM.e.find('[name="host"]').val();
    e.protocol=$.aM.e.find('[name="protocol"]').val();
    e.port=$.aM.e.find('[name="port"]').val();
    e.path=$.aM.e.find('[name="path"]').val();
    if($.aM.e.find('[name="type"]').val()==='local'){
        e.url=e.path;
    }else{
        if(e.host.indexOf('@')===-1&&e.user!==''){
            e.host=e.user+':'+e.pass+'@'+e.host;
        }
        e.url=$.ccio.init('url',e)+e.path;
    }
    $.pB.e.find('[name="url"]').val(e.url);
    $.pB.f.submit();
    $.pB.e.modal('show');
})
$.aM.e.find('.import_config').click(function(e){
  var e={};e.e=$(this);e.mid=e.e.parents('[mid]').attr('mid');
    $.confirm.e.modal('show');
    $.confirm.title.text('<%-cleanLang(lang['Import Monitor Configuration'])%>')
    e.html='<%-cleanLang(lang.ImportMonitorConfigurationText)%><div style="margin-top:15px"><div class="form-group"><textarea placeholder="<%-cleanLang(lang['Paste JSON here.'])%>" class="form-control"></textarea></div><label class="upload_file btn btn-primary btn-block"> Upload File <input class="upload" type=file name="files[]"></label></div>';
    $.confirm.body.html(e.html)
    $.confirm.e.find('.upload').change(function(e){
        var files = e.target.files; // FileList object
        f = files[0];
        var reader = new FileReader();
        reader.onload = function(ee) {
            $.confirm.e.find('textarea').val(ee.target.result);
        }
        reader.readAsText(f);
    });
    $.confirm.click({title:'Import',class:'btn-primary'},function(){
        try{
            e.values=JSON.parse($.confirm.e.find('textarea').val());
            $.aM.import(e)
            $.aM.e.modal('show')
        }catch(err){
            $.ccio.log(err)
            $.ccio.init('note',{title:'<%-cleanLang(lang['Invalid JSON'])%>',text:'<%-cleanLang(lang.InvalidJSONText)%>',type:'error'})
        }
    });
});
$.aM.e.find('.save_config').click(function(e){
  var e={};e.e=$(this);e.mid=e.e.parents('[mid]').attr('mid');e.s=$.aM.f.serializeObject();
    if(!e.mid||e.mid===''){
        e.mid='NewMonitor'
    }
    e.dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(e.s));
    $('#temp').html('<a></a>')
        .find('a')
        .attr('href',e.dataStr)
        .attr('download','Shinobi_'+e.mid+'_config.json')
        [0].click()
});
$.aM.e.find('.add_map').click(function(e){
    $('[input-mapping]').show()
    $.ccio.tm('input-map')
});
$.aM.e.find('.add_channel').click(function(e){
    $.ccio.tm('stream-channel')
});
$.aM.f.find('[detail="stream_type"]').change(function(e){
    e.e=$(this);
    if(e.e.val()==='jpeg'){$.aM.f.find('[detail="snap"]').val('1').change()}
})
$.aM.f.find('[name="type"]').change(function(e){
    e.e=$(this);
    if(e.e.val()==='h264'){$.aM.f.find('[name="protocol"]').val('rtsp').change()}
})
$.aM.md=$.aM.f.find('[detail]');
$.aM.md.change($.ccio.form.details)
$.aM.f.on('change','[selector]',function(){
    e={e:$(this)}
    e.v=e.e.val();
    e.a=e.e.attr('selector')
    e.triggerChange=e.e.attr('triggerchange')
    $.aM.f.find('.'+e.a+'_input').hide()
    $.aM.f.find('.'+e.a+'_'+e.v).show();
    $.aM.f.find('.'+e.a+'_text').text($(this).find('option:selected').text())
    if(e.triggerChange&&e.triggerChange!==''){
        console.log(e.triggerChange)
        $(e.triggerChange).trigger('change')
    }
    $.aM.drawList()
});
$.aM.f.find('[name="type"]').change(function(e){
    e.e=$(this);
    e.v=e.e.val();
    e.h=$.aM.f.find('[name="path"]');
    e.p=e.e.parents('.form-group');
    switch(e.v){
        case'local':case'socket':
            e.h.attr('placeholder','/dev/video0')
        break;
        default:
            e.h.attr('placeholder','/videostream.cgi?1')
        break;
    }
});
//api window
$.apM={e:$('#apis')};$.apM.f=$.apM.e.find('form');
$.apM.md=$.apM.f.find('[detail]');
$.apM.md.change($.ccio.form.details).first().change();
$.apM.f.submit(function(e){
    e.preventDefault();e.e=$(this),e.s=e.e.serializeObject();
    e.er=[];
    if(!e.s.ip||e.s.ip.length<7){e.er.push('Enter atleast one IP')}
    if(e.er.length>0){$.apM.e.find('.msg').html(e.er.join('<br>'));return;}
    $.each(e.s,function(n,v){e.s[n]=v.trim()})
    $.ccio.cx({f:'api',ff:'add',form:e.s})
});
$.apM.e.on('click','.delete',function(e){
    e.e=$(this);e.p=e.e.parents('[api_key]'),e.code=e.p.attr('api_key');
    $.confirm.e.modal('show');
    $.confirm.title.text('Delete API Key');
    e.html='Do you want to delete this API key? You cannot recover it.';
    $.confirm.body.html(e.html);
    $.confirm.click({title:'Delete',class:'btn-danger'},function(){
        $.ccio.cx({f:'api',ff:'delete',form:{code:e.code}})
    });
})
//filters window
if(!$user.details.filters)$user.details.filters={};
$.fI={e:$('#filters')};$.fI.f=$.fI.e.find('form');
$.fI.md=$.fI.f.find('[detail]');
$.ccio.init('filters');
$.ccio.tm('filters-where');
$.fI.e.on('click','.where .add',function(e){
    $.ccio.tm('filters-where');
})
$.fI.e.on('click','.where .remove',function(e){
    e.e=$('#filters_where .row');
    if(e.e.length>1){
        e.e.last().remove();
    }
})
$('#saved_filters').change(function(e){
    e.e=$(this),e.id=e.e.val();
    $('#filters_where').empty()
    if(e.id&&e.id!==''){
        e.name=$user.details.filters[e.id].name;
        $.each($user.details.filters[e.id].where,function(n,v){
            $.ccio.tm('filters-where',v)
        });
        $.each($user.details.filters[e.id],function(n,v){
            if(n==='where'){return}
            $.fI.f.find('[name="'+n+'"]').val(v);
        });
    }else{
        e.name='<%-cleanLang(lang['Add New'])%>';
        $.fI.f.find('[name="id"]').val($.ccio.gid(5));
        $.ccio.tm('filters-where');
    }
    $.fI.e.find('.filter_name').text(e.name)
}).change()
$.fI.f.find('.delete').click(function(e){
    e.s=$.fI.f.serializeObject();
    $.confirm.e.modal('show');
    $.confirm.title.text('<%-cleanLang(lang['Delete Filter'])%>');
    e.html='<%-cleanLang(lang.confirmDeleteFilter)%>';
    $.confirm.body.html(e.html);
    $.confirm.click({title:'<%-cleanLang(lang['Delete Filter'])%>',class:'btn-danger'},function(){
        $.ccio.cx({f:'settings',ff:'filters',fff:'delete',form:e.s})
    });
})
$.fI.f.submit(function(e){
    e.preventDefault();e.e=$(this),e.s=e.e.serializeObject();
    e.er=[];
    $.each(e.s,function(n,v){e.s[n]=v.trim()})
    e.s.where=[];
    $('.where-row').each(function(n,v){
        n={};
        $(v).find('[where]').each(function(m,b){
            b=$(b);
            n[b.attr('where')]=b.val();
        })
        e.s.where.push(n)
    })
    $.ccio.cx({f:'settings',ff:'filters',fff:'save',form:e.s})
});
//settings window
$.sM={e:$('#settings')};
$.sM.f=$.sM.e.find('form');
$.sM.links=$('#linkShinobi');
$.sM.g=$('#settings_mon_groups');
$.sM.md=$.sM.f.find('[detail]');
$.sM.md.change($.ccio.form.details);
$.sM.f.find('[selector]').change(function(e){
    e.v=$(this).val();e.a=$(this).attr('selector')
    $.sM.f.find('.'+e.a+'_input').hide()
    $.sM.f.find('.'+e.a+'_'+e.v).show();
    $.sM.f.find('.'+e.a+'_text').text($(this).find('option:selected').text())
});
$.sM.writewMonGroups=function(){
    $.sM.f.find('[detail="mon_groups"]').val(JSON.stringify($user.mon_groups)).change()
}
$.sM.reDrawMonGroups=function(){
    $.sM.g.empty();
    $.ccio.pm('option',$user.mon_groups,'#settings_mon_groups')
    $.sM.g.change();
};
$.sM.f.submit(function(e){
    e.preventDefault();
    $.sM.writewMonGroups()
    $.sM.linkChange()
    e.e=$(this),e.s=e.e.serializeObject();
    e.er=[];
    if(e.s.pass!==''&&e.password_again===e.s.pass){e.er.push("<%-lang["Passwords don't match"]%>")};
    if(e.er.length>0){$.sM.e.find('.msg').html(e.er.join('<br>'));return;}
    $.each(e.s,function(n,v){e.s[n]=v.trim()})
    $.ccio.cx({f:'settings',ff:'edit',form:e.s})
    $.sM.e.modal('hide')
});
$.sM.e.on('shown.bs.modal',function(){
    $.sM.reDrawMonGroups()
})
$.sM.g.change(function(e){
    e.v=$(this).val();
    e.group=$user.mon_groups[e.v];
    if(!e.group){return}
    $.sM.selectedMonGroup=e.group;
    $.each(e.group,function(n,v){
        $.sM.f.find('[group="'+n+'"]').val(v)
    })
});
$.sM.f.find('[groups]').change(function(e){
    e.v=$.sM.g.val();
    if(!e.v||e.v==''){
        e.e=$.sM.f.find('[group="name"]')
        e.name=e.e.val()
        $('.mon_groups .add').click();
        e.v=$.sM.g.val()
        e.e.val(e.name)
    }
    e.group=$user.mon_groups[e.v];
    $.sM.f.find('[groups]').each(function(n,v){
        v=$(v)
        e.group[v.attr('groups')]=v.val()
    });
    $user.mon_groups[e.v]=e.group;
    $.sM.g.find('option[value="'+$.sM.g.val()+'"]').text(e.group.name)
    $.sM.writewMonGroups()
})
$.sM.f.on('click','.mon_groups .delete',function(e){
    e.v=$.sM.g.val();
    delete($user.mon_groups[e.v]);
    $.sM.reDrawMonGroups()
})
$.sM.f.on('click','.mon_groups .add',function(e){
    e.gid=$.ccio.gid(5);
    $user.mon_groups[e.gid]={id:e.gid,name:e.gid};
    $.sM.g.append($.ccio.tm('option',$user.mon_groups[e.gid]));
    $.sM.g.val(e.gid)
    $.sM.g.change();
});
$.sM.linkChange=function(){
    var e={};
    e.e=$.sM.e.find('[name="details"]')
    e.details=JSON.parse(e.e.val())
    e.details.links=[]
    $.sM.links.find('.linksGroup').each(function(n,v){
        var arr={}
        $(v).find('[link]').each(function(m,b){
            arr[$(b).attr('link')]=$(b).val()
        })
        e.details.links.push(arr)
    })
    e.e.val(JSON.stringify(e.details))
}
$.sM.f.on('change','[link]',$.sM.linkChange)
$.sM.e.on('click','.linkShinobi .delete',function(){
    $(this).parents('.linksGroup').remove()
    $.sM.linkChange()
})
$.sM.e.find('.linkShinobi .add').click(function(){
    $.ccio.tm('link-set',{},'#linkShinobi')
    $.sM.linkChange()
})
//videos window
$.vidview={e:$('#videos_viewer'),pages:$('#videos_viewer_pages'),limit:$('#videos_viewer_limit'),dr:$('#videos_viewer_daterange'),preview:$('#videos_viewer_preview')};
$.vidview.f=$.vidview.e.find('form')
$.vidview.dr.daterangepicker({
    startDate:moment().subtract(moment.duration("24:00:00")),
    endDate:moment().add(moment.duration("24:00:00")),
    timePicker: true,
    timePickerIncrement: 30,
    locale: {
        format: 'MM/DD/YYYY h:mm A'
    }
},function(start, end, label){
    $.vidview.launcher.click()
    $.vidview.dr.focus()
});
$.vidview.e.on('change','#videos_select_all',function(e){
    e.e=$(this);
    e.p=e.e.prop('checked')
    e.a=$.vidview.e.find('input[type=checkbox][name]')
    if(e.p===true){
        e.a.prop('checked',true)
    }else{
        e.a.prop('checked',false)
    }
})
$.vidview.f.submit(function(e){
    e.preventDefault();
    $.vidview.launcher.click()
    return false;
})
$('#videos_viewer_limit,#videos_viewer_daterange').change(function(){
    $.vidview.f.submit()
})
$.vidview.e.find('.delete_selected').click(function(e){
    e.s={}
    $.vidview.f.find('[data-ke] input:checked').each(function(n,v){
        v=$(v).parents('tr')
        e.s[v.attr('data-file')]={mid:v.attr('data-mid'),auth:v.attr('data-auth')}
    })
    $.confirm.e.modal('show');
    $.confirm.title.text('<%-cleanLang(lang['Delete Selected Videos'])%>')
    e.html='<%-cleanLang(lang.DeleteSelectedVideosMsg)%><div style="margin-bottom:15px"></div>'
    $.each(e.s,function(n,v){
        e.html+=n+'<br>';
    })
    $.confirm.body.html(e.html)
    $.confirm.click({title:'Delete Video',class:'btn-danger'},function(){
        $.each(e.s,function(n,v){
            $.getJSON($.ccio.init('location',$.users[v.auth])+v.auth+'/videos/'+v.ke+'/'+v.mid+'/'+n+'/delete',function(d){
                $.ccio.log(d)
            })
        })
    });
})
$.vidview.pages.on('click','[page]',function(e){
    e.limit=$.vidview.limit.val();
    e.page=$(this).attr('page');
    $.vidview.current_page=e.page;
    if(e.limit.replace(/ /g,'')===''){
        e.limit='100';
    }
    if(e.limit.indexOf(',')>-1){
        e.limit=parseInt(e.limit.split(',')[1])
    }else{
        e.limit=parseInt(e.limit)
    }
    $.vidview.limit.val((parseInt(e.page)-1)+'00,'+e.limit)
    $.vidview.launcher.click()
})
$.vidview.e.on('click','.preview',function(e){
    e.preventDefault()
    e=$(this)
    $.vidview.preview.html('<video class="video_video" video="'+e.attr('href')+'" preload controls autoplay><source src="'+e.attr('href')+'" type="video/mp4"></video>')
})
//Timelapse Window
$.timelapse={e:$('#timelapse')}
$.timelapse.f=$.timelapse.e.find('form'),
$.timelapse.meter=$.timelapse.e.find('.motion-meter'),
$.timelapse.line=$('#timelapse_video_line'),
$.timelapse.display=$('#timelapse_video_display'),
$.timelapse.seekBar=$('#timelapse_seekBar'),
$.timelapse.seekBarProgress=$.timelapse.seekBar.find('.progress-bar'),
$.timelapse.dr=$('#timelapse_daterange'),
$.timelapse.mL=$.timelapse.e.find('.motion_list'),
$.timelapse.monitors=$.timelapse.e.find('.monitors_list');
$.timelapse.playDirection='videoAfter'
$.timelapse.playRate=15
$.timelapse.placeholder=placeholder.getData(placeholder.plcimg({bgcolor:'#b57d00',text:'...'}))
$.timelapse.dr.daterangepicker({
    startDate:moment().subtract(moment.duration("24:00:00")),
    endDate:moment().add(moment.duration("24:00:00")),
    timePicker: true,
    timePickerIncrement: 30,
    locale: {
        format: 'MM/DD/YYYY h:mm A'
    }
},function(start, end, label){
    $.timelapse.drawTimeline()
    $.timelapse.dr.focus()
});
$.timelapse.f.find('input,select').change(function(){
    $.timelapse.f.submit()
})
$.timelapse.f.submit(function(e){
    e.preventDefault();
    $.timelapse.drawTimeline()
    return false;
})
$.timelapse.drawTimeline=function(getData){
    var e={};
    if(getData===undefined){getData=true}
    var mid=$.timelapse.monitors.val();
    e.dateRange=$.timelapse.dr.data('daterangepicker');
    e.dateRange={startDate:e.dateRange.startDate,endDate:e.dateRange.endDate}
    e.videoURL='/'+$user.auth_token+'/videos/'+$user.ke+'/'+mid;
    e.videoURL+='?limit=100&start='+$.ccio.init('th',e.dateRange.startDate)+'&end='+$.ccio.init('th',e.dateRange.endDate);
    e.next=function(videos){
        $.timelapse.currentVideos={}
        e.tmp=''
        $.each(videos.videos,function(n,v){
            if(!v||!v.time){return}
            v.filename=$.ccio.init('tf',v.time)+'.'+v.ext;
            v.videoBefore=videos.videos[n-1];
            v.videoAfter=videos.videos[n+1];
//            if(v.href.charAt(0)==='/'){
//                v.href=$.ccio.init('location',user)+(v.href.substring(1))
//                v.videoURL=$.ccio.init('location',user)+(v.videoURL.substring(1))
//            }
            v.downloadLink=v.href+'?downloadName='+v.mid+'-'+v.filename
            v.position=n;
            $.timelapse.currentVideos[v.filename]=v;
            e.tmp+='<li class="glM'+v.mid+$user.auth_token+' list-group-item timelapse_video flex-block" timelapse="video" file="'+v.filename+'" href="'+v.href+'" mid="'+v.mid+'" ke="'+v.ke+'" auth="'+$user.auth_token+'">'
            e.tmp+='<div class="flex-block">'
            e.tmp+='<div class="flex-unit-3"><div class="frame" style="background-image:url('+$.timelapse.placeholder+')"></div></div>'
            e.tmp+='<div class="flex-unit-3"><div><span title="'+v.time+'" class="livestamp"></span></div><div>'+v.filename+'</div></div>'
            e.tmp+='<div class="flex-unit-3 text-right"><a class="btn btn-default" download="'+v.mid+'-'+v.filename+'" href="'+v.href+'?downloadName='+v.mid+'-'+v.filename+'">&nbsp;<i class="fa fa-download"></i>&nbsp;</a> <a class="btn btn-danger" video="delete">&nbsp;<i class="fa fa-trash-o"></i>&nbsp;</a></div>'
            e.tmp+='</div>'
            e.tmp+='<div class="flex-block">'
            e.tmp+='<div class="flex-unit-3"><div class="progress"><div class="progress-bar progress-bar-primary" role="progressbar" style="width:0%"></div></div></div>'
            e.tmp+='</div>'
            e.tmp+='</li>'
        })
        $.timelapse.line.html(e.tmp)
        $.ccio.init('ls')
        if(getData===true){
            e.timeout=50
        }else{
            e.timeout=2000
        }
        setTimeout(function(){
            if($.timelapse.e.find('.timelapse_video.active').length===0){
                $.timelapse.e.find('[timelapse="video"]').first().click()
            }
        },e.timeout)
    }
    if(getData===true){
        $.getJSON(e.videoURL,function(videos){
            videos.videos=videos.videos.reverse()
            $.timelapse.currentVideosArray=videos
            e.next(videos)
        })
    }else{
        e.next($.timelapse.currentVideosArray)
    }
}
$.timelapse.e.on('click','[timelapse]',function(){
    var e={}
    e.e=$(this)
    e.videoCurrentNow=$.timelapse.display.find('.videoNow')
    e.videoCurrentAfter=$.timelapse.display.find('.videoAfter')
    e.videoCurrentBefore=$.timelapse.display.find('.videoBefore')
    if($.timelapse.videoInterval){
        clearInterval($.timelapse.videoInterval);
    }
    switch(e.e.attr('timelapse')){
        case'download':
            $.timelapse.line.find('.active [download]').click()
        break;
        case'mute':
            e.videoCurrentNow[0].muted = !e.videoCurrentNow[0].muted
            $.timelapse.videoNowIsMuted = e.videoCurrentNow[0].muted
            e.e.find('i').toggleClass('fa-volume-off fa-volume-up')
            e.e.toggleClass('btn-danger')
        break;
        case'play':
            $.timelapse.playRate =5
            e.videoCurrentNow[0].playbackRate = $.timelapse.playRate;
            $.timelapse.onPlayPause(1)
        break;
        case'stepFrontFront':
            e.add=e.e.attr('add')
            e.stepFrontFront=parseInt(e.e.attr('stepFrontFront'))
            if(!e.stepFrontFront||isNaN(e.stepFrontFront)){e.stepFrontFront = 5}
            if(e.add==="0"){
                $.timelapse.playRate = e.stepFrontFront
            }else{
                $.timelapse.playRate += e.stepFrontFront
            }
            e.videoCurrentNow[0].playbackRate = $.timelapse.playRate;
            e.videoCurrentNow[0].play()
        break;
        case'stepFront':
            e.videoCurrentNow[0].currentTime += 5;
            e.videoCurrentNow[0].pause()
        break;
        case'stepBackBack':
           $.timelapse.videoInterval = setInterval(function(){
               $.timelapse.playRate = 5
               e.videoCurrentNow[0].playbackRate = $.timelapse.playRate;
               if(e.videoCurrentNow[0].currentTime == 0){
                   clearInterval($.timelapse.videoInterval);
                   e.videoCurrentNow[0].pause();
               }
               else{
                   e.videoCurrentNow[0].currentTime += -.5;
               }
           },30);
        break;
        case'stepBack':
            e.videoCurrentNow[0].currentTime += -5;
            e.videoCurrentNow[0].pause()
        break;
        case'video':
            $.timelapse.e.find('video').each(function(n,v){
                v.pause()
            })
            e.playButtonIcon=$.timelapse.e.find('[timelapse="play"]').find('i')
            e.drawVideoHTML=function(position){
                var video
                var exisitingElement=$.timelapse.display.find('.'+position)
                if(position){
                    video=e.video[position]
                }else{
                    position='videoNow'
                    video=e.video
                }
                if(video){
                   $.timelapse.display.append('<video class="video_video '+position+'" video="'+video.href+'" preload><source src="'+video.href+'" type="video/'+video.ext+'"></video>')
                }
            }
            e.filename=e.e.attr('file')
            e.video=$.timelapse.currentVideos[e.filename]
            e.videoIsSame=(e.video.href==e.videoCurrentNow.attr('video'))
            e.videoIsAfter=(e.video.href==e.videoCurrentAfter.attr('video'))
            e.videoIsBefore=(e.video.href==e.videoCurrentBefore.attr('video'))
            if(e.videoIsSame||e.videoIsAfter||e.videoIsBefore){
                switch(true){
                    case e.videoIsSame:
                        $.ccio.log('$.timelapse','videoIsSame')
                        e.videoNow=$.timelapse.display.find('video.videoNow')
                        if(e.videoNow[0].paused===true){
                            e.videoNow[0].play()
                        }else{
                            e.videoNow[0].pause()
                        }
                        return
                    break;
                    case e.videoIsAfter:
                        $.ccio.log('$.timelapse','videoIsAfter')
                        e.videoCurrentBefore.remove()
                        e.videoCurrentAfter.removeClass('videoAfter').addClass('videoNow')
                        e.videoCurrentNow.removeClass('videoNow').addClass('videoBefore')
                        e.drawVideoHTML('videoAfter')
                    break;
                    case e.videoIsBefore:
                        $.ccio.log('$.timelapse','videoIsBefore')
                        e.videoCurrentAfter.remove()
                        e.videoCurrentBefore.removeClass('videoBefore').addClass('videoNow')
                        e.videoCurrentNow.removeClass('videoNow').addClass('videoAfter')
                        e.drawVideoHTML('videoBefore')
                    break;
                }
            }else{
                $.ccio.log('$.timelapse','newSetOf3')
                $.timelapse.display.empty()
                e.drawVideoHTML()//videoNow
                e.drawVideoHTML('videoBefore')
                e.drawVideoHTML('videoAfter')
            }
            $.timelapse.display.find('video').each(function(n,v){
                v.addEventListener('loadeddata', function() {
                    e.videoCurrentAfterPreview=$('.timelapse_video[href="'+$(v).attr('video')+'"] .frame')
                    if(e.videoCurrentAfterPreview.attr('set')!=='1'){
                        $.ccio.snapshotVideo(v,function(url,buffer){
                            e.videoCurrentAfterPreview.attr('set','1').css('background-image','url('+url+')')
                            if($(v).hasClass('videoAfter')){
                                v.currentTime=0
                                v.pause()
                            }
                        })
                    }
                }, false);
            })
            e.videoNow=$.timelapse.display.find('video.videoNow')[0]
            if($.timelapse.videoNowIsMuted){
                e.videoNow.muted=true
            }
            e.videoNow.playbackRate = $.timelapse.playRate
            e.videoNow.play()
            e.playButtonIcon.removeClass('fa-pause').addClass('fa-play')
            $.timelapse.onended = function() {
                $.timelapse.line.find('[file="'+e.video[$.timelapse.playDirection].filename+'"]').click()
            };
            e.videoNow.onended = $.timelapse.onended
            e.videoNow.onerror = $.timelapse.onended
            $.timelapse.onPlayPause=function(x){
                if(e.videoNow.paused===true){
                    e.playButtonIcon.removeClass('fa-pause').addClass('fa-play')
                    if(x==1)e.videoNow.play();
                }else{
                    e.playButtonIcon.removeClass('fa-play').addClass('fa-pause')
                    if(x==1)e.videoNow.pause();
                }
            }
            $(e.videoNow)
            .off('play').on('play',$.timelapse.onPlayPause)
            .off('pause').on('pause',$.timelapse.onPlayPause)
            .off('timeupdate').on('timeupdate',function(){
                var value= (( e.videoNow.currentTime / e.videoNow.duration ) * 100)+"%"
                $.timelapse.seekBarProgress.css("width",value);
                $.timelapse.e.find('.timelapse_video[file="'+e.filename+'"] .progress-bar').css("width",value);
            })
            $.timelapse.seekBar.off("click").on("click", function(seek){
                var offset = $(this).offset();
                var left = (seek.pageX - offset.left);
                var totalWidth = $.timelapse.seekBar.width();
                var percentage = ( left / totalWidth );
                var vidTime = e.videoNow.duration * percentage;
                e.videoNow.currentTime = vidTime;
            });
            
            $.ccio.log('$.timelapse',e.video)
            $.timelapse.line.find('.timelapse_video').removeClass('active')
            e.videoCurrentNow=$.timelapse.display.find('.videoNow')
            e.e.addClass('active')
            if ($('#timelapse_video_line:hover').length === 0) {
                $.timelapse.line.animate({scrollTop:$.timelapse.line.scrollTop() + e.e.position().top - $.timelapse.line.height()/2 + e.e.height()/2 - 40});
            }
        break;
    }
    $.timelapse.e.find('.timelapse_playRate').text('x'+$.timelapse.playRate)
})
$.timelapse.e.on('hidden.bs.modal',function(e){
    delete($.timelapse.currentVideos)
    delete($.timelapse.currentVideosArray)
})
//POWER videos window
$.pwrvid={e:$('#pvideo_viewer')};
$.pwrvid.f=$.pwrvid.e.find('form'),
$.pwrvid.d=$('#vis_pwrvideo'),
$.pwrvid.mL=$('#motion_list'),
$.pwrvid.m=$('#vis_monitors'),
$.pwrvid.lv=$('#live_view'),
$.pwrvid.dr=$('#pvideo_daterange'),
$.pwrvid.vp=$('#video_preview'),
$.pwrvid.seekBar=$('#pwrvid_seekBar'),
$.pwrvid.seekBarProgress=$.pwrvid.seekBar.find('.progress-bar'),
$.pwrvid.playRate = 1;
$.pwrvid.dr.daterangepicker({
    startDate:moment().subtract(moment.duration("24:00:00")),
    endDate:moment().add(moment.duration("24:00:00")),
    timePicker: true,
    timePickerIncrement: 30,
    locale: {
        format: 'MM/DD/YYYY h:mm A'
    }
},function(start, end, label){
    $.pwrvid.drawTimeline()
    $.pwrvid.dr.focus()
});
$('#pvideo_show_events').change(function(){
    $.pwrvid.drawTimeline()
})
$.pwrvid.e.on('click','[preview]',function(e){
    e.e=$(this);
    e.video=$.pwrvid.vp.find('video')[0];
    if(e.video){
        e.duration=e.video.duration;
        e.now=e.video.currentTime;
    }
    if($.pwrvid.video){
        clearInterval($.pwrvid.video.interval);
    }
    switch(e.e.attr('preview')){
        case'fullscreen':
            $.ccio.init('fullscreen',e.video)
        break;
        case'mute':
            e.video.muted = !e.video.muted
            e.e.find('i').toggleClass('fa-volume-off fa-volume-up')
            e.e.toggleClass('btn-danger')
        break;
        case'play':
            e.video.playbackRate = 1;
            $.pwrvid.vpOnPlayPause(1)
        break;
        case'stepFrontFront':
            e.add=e.e.attr('add')
            e.stepFrontFront=parseInt(e.e.attr('stepFrontFront'))
            if(!e.stepFrontFront||isNaN(e.stepFrontFront)){e.stepFrontFront = 5}
            if(e.add==="0"){
                $.pwrvid.playRate = e.stepFrontFront
            }else{
                $.pwrvid.playRate += e.stepFrontFront
            }
            e.video.playbackRate = $.pwrvid.playRate;
            e.video.play()
        break;
        case'stepFront':
            e.video.currentTime += 1;
            e.video.pause()
        break;
        case'stepBackBack':
           $.pwrvid.video.interval = setInterval(function(){
               e.video.playbackRate = 1.0;
               if(e.video.currentTime == 0){
                   clearInterval($.pwrvid.video.interval);
                   e.video.pause();
               }
               else{
                   e.video.currentTime += -.2;
               }
           },30);
        break;
        case'stepBack':
            e.video.currentTime += -1;
            e.video.pause()
        break;
        case'video':
//            e.preventDefault();
            e.p=e.e.parents('[mid]');
            e.filename=e.p.attr('file');
            $.pwrvid.vp.find('h3').text(e.filename)
            e.href=e.e.attr('href');
            e.status=e.p.attr('status');
            e.mon=$.ccio.mon[e.p.attr('ke')+e.p.attr('mid')+$user.auth_token];
            $.pwrvid.vp.find('.holder').html('<video class="video_video" video="'+e.href+'"><source src="'+e.href+'" type="video/'+e.mon.ext+'"></video>');
            $.pwrvid.vp
                .attr('mid',e.mon.mid)
                .attr('mid',e.mon.user.auth_token)
                .attr('ke',e.mon.ke)
                .attr('status',e.status)
                .attr('file',e.filename)
                .find('[download],[video="download"]')
                .attr('download',e.filename)
                .attr('href',e.href)
                $.pwrvid.vp.find('video').off('loadeddata').on('loadeddata',function(){
                    $.pwrvid.vp.find('.stream-objects .stream-detected-object').remove()
                })
            if(e.status==1){
                $.get(e.href.split('?')[0]+'/status/2',function(d){
                })
            }
            var labels=[]
            var Dataset1=[]
            var events=$.pwrvid.currentDataObject[e.filename].motion
            var eventsLabeledByTime={}
            $.each(events,function(n,v){
                if(!v.details.confidence){v.details.confidence=0}
                var time=moment(v.time).format('MM/DD/YYYY HH:mm:ss')
                labels.push(time)
                Dataset1.push(v.details.confidence)
                eventsLabeledByTime[time]=v;
            })
            if(events.length>0){
                $.pwrvid.mL.html("<canvas></canvas>")
                var timeFormat = 'MM/DD/YYYY HH:mm:ss';
                var color = Chart.helpers.color;
                Chart.defaults.global.defaultFontColor = '#fff';
                var config = {
                    type: 'bar',
                    data: {
                        labels: labels,
                        datasets: [{
                            type: 'line',
                            label: 'Motion Confidence',
                            backgroundColor: color(window.chartColors.red).alpha(0.2).rgbString(),
                            borderColor: window.chartColors.red,
                            data: Dataset1,
                        }]
                    },
                    options: {
                        maintainAspectRatio: false,
                        title: {
                            fontColor: "white",
                            text:"Events in this video"
                        },
                        scales: {
                            xAxes: [{
                                type: "time",
                                display: true,
                                time: {
                                    format: timeFormat,
                                    // round: 'day'
                                }
                            }],
                        },
                    }
                };
                var ctx = $.pwrvid.mL.find('canvas')[0].getContext("2d");
                $.pwrvid.miniChart = new Chart(ctx, config);
                $.pwrvid.mL.find('canvas').click(function(f) {
                    var target = $.pwrvid.miniChart.getElementsAtEvent(f)[0];
                    if(!target){return false}
                    var video = $.pwrvid.currentDataObject[e.filename];
                    var event = video.motion[target._index];
                    var video1 = $('#video_preview video')[0];
                    video1.currentTime=moment(event.time).diff(moment(video.row.time),'seconds')
                    video1.play()
                });
                var colorNames = Object.keys(window.chartColors);

            }else{
                $.pwrvid.mL.html('<div class="super-center text-center" style="width:auto"><%-cleanLang(lang['No Events found for this video'])%></div>')
            }
            $.pwrvid.video={filename:e.filename,href:e.href,mid:e.mon.mid,ke:e.mon.ke}
            $.pwrvid.vpOnPlayPause=function(x,e){
              var e={}
                e.video=$.pwrvid.vp.find('video')[0]
                e.i=$.pwrvid.vp.find('[preview="play"]').find('i')
                if(e.video.paused===true){
                    e.i.removeClass('fa-pause').addClass('fa-play')
                    if(x==1)e.video.play();
                }else{
                    e.i.removeClass('fa-play').addClass('fa-pause')
                    if(x==1)e.video.pause();
                }
            }
            var videoElement=$.pwrvid.vp.find('video')[0]
            $.pwrvid.vp.find('video')
                .off('loadeddata').on('loadeddata', function() {
                    this.playbackRate = $.pwrvid.playRate;
                    this.play()
                })
                .off("pause").on("pause",$.pwrvid.vpOnPlayPause)
                .off("play").on("play",$.pwrvid.vpOnPlayPause)
                .off("timeupdate").on("timeupdate",function(){
                    var video = $.pwrvid.currentDataObject[e.filename];
                    var videoTime=moment(video.row.time).add(parseInt(videoElement.currentTime),'seconds').format('MM/DD/YYYY HH:mm:ss');
                    var event = eventsLabeledByTime[videoTime];
                    if(event){
                        if(event.details.plates){
                            console.log('licensePlateVideo',event)
                        }
                        if(event.details.matrices){
                            event.monitorDetails=JSON.parse(e.mon.details)
                            event.stream=$(videoElement)
                            event.streamObjects=$.pwrvid.vp.find('.stream-objects')
                            $.ccio.init('drawMatrices',event)
                        }
                        if(event.details.confidence){
                            $.pwrvid.vp.find('.motion-meter .progress-bar').css('width',event.details.confidence+'px').find('span').text(event.details.confidence)
                        }
                    }
                    var value= (( videoElement.currentTime / videoElement.duration ) * 100)+"%"
                    $.pwrvid.seekBarProgress.css("width",value);
                })
                $.pwrvid.seekBar.off("click").on("click", function(seek){
                    var offset = $(this).offset();
                    var left = (seek.pageX - offset.left);
                    var totalWidth = $.pwrvid.seekBar.width();
                    var percentage = ( left / totalWidth );
                    var vidTime = videoElement.duration * percentage;
                    videoElement.currentTime = vidTime;
                });
        break;
    }
})
$.pwrvid.drawTimeline=function(getData){
    var e={};
    $.pwrvid.e.find('.nodata').hide()
    if(getData===undefined){getData=true}
    var mid=$.pwrvid.m.val();
    $.pwrvid.e.find('.loading').show()
    e.live_header=$.pwrvid.lv.find('h3 span');
    e.live=$.pwrvid.lv.find('iframe');
    e.dateRange=$.pwrvid.dr.data('daterangepicker');
    if(e.eventLimit===''){e.eventLimit=500}
    if(e.videoLimit===''){e.videoLimit=0}
    e.live_header.text($.ccio.mon[$user.ke+mid+$user.auth_token].name)
    e.live.attr('src','/'+$user.auth_token+'/embed/'+$user.ke+'/'+mid+'/fullscreen|jquery|relative|gui')

    var pulseLoading = function(){
        var loading = $.pwrvid.e.find('.loading')
        var currentColor = loading.css('color')
        loading.animate('color','red')
        setTimeout(function(){
            loading.css('color',currentColor)
        },500)
    }
    if(getData===true){
        $.ccio.cx({
            f:'monitor',
            ff:'get',
            fff:'videos&events',
            videoLimit:$('#pvideo_video_limit').val(),
            eventLimit:$('#pvideo_event_limit').val(),
            startDate:$.ccio.init('th',e.dateRange.startDate),
            endDate:$.ccio.init('th',e.dateRange.endDate),
            ke:e.ke,
            mid:mid
        });
    }else{
        $.pwrvid.e.find('.loading').hide()
        e.next($.pwrvid.currentVideos,$.pwrvid.currentEvents)
    }
}
$('#vis_monitors,#pvideo_event_limit,#pvideo_video_limit').change(function(){
    $.pwrvid.f.submit()
})
$.pwrvid.f.submit(function(e){
    e.preventDefault();
    $.pwrvid.drawTimeline()
    return false;
})
$.pwrvid.e.on('hidden.bs.modal',function(e){
    $(this).find('iframe').attr('src','about:blank')
    $.pwrvid.vp.find('.holder').empty()
    delete($.pwrvid.currentDataObject)
    delete($.pwrvid.currentData)
    $.pwrvid.mL.empty()
    $.pwrvid.d.empty()
})
//open all monitors
$('[class_toggle="list-blocks"][data-target="#left_menu"]').dblclick(function(){
    $('#monitors_list [monitor="watch"]').click()
})
//search monitors list
$('#monitors_list_search').keyup(function(){
    var monitorBlocks = $('.monitor_block');
    var searchTerms = $(this).val().toLowerCase().split(' ')
    if(searchTerms.length === 0 || searchTerms[0] === ''){
        monitorBlocks.show()
        return
    }
    monitorBlocks.hide()
    $.each($.ccio.mon,function(n,monitor){
        var searchThis = JSON.stringify($.ccio.init('cleanMon',monitor)).toLowerCase().replace('"','');
        console.log(searchTerms,searchThis)
        $.each(searchTerms,function(m,term){
            if(searchThis.indexOf(term) >-1 ){
                $('.monitor_block[ke="'+monitor.ke+'"][mid="'+monitor.mid+'"]').show()
            }
        })
    })
})
//dynamic bindings
$('body')
.on('click','.logout',function(e){
    var logout = function(user,callback){
        $.get('/'+user.auth_token+'/logout/'+user.ke+'/'+user.uid,callback)
    }
    $.each($.users,function(n,linkedShinobiUser){
        logout(linkedShinobiUser,function(){});
    })
    logout($user,function(data){
        console.log(data)
        localStorage.removeItem('ShinobiLogin_'+location.host);
        location.href=location.href;
    });
})
.on('click','[video]',function(e){
    e.e=$(this),
    e.a=e.e.attr('video'),
    e.p=e.e.parents('[mid]'),
    e.ke=e.p.attr('ke'),
    e.mid=e.p.attr('mid'),
    e.file=e.p.attr('file');
    e.auth=e.p.attr('auth');
    e.status=e.p.attr('status');
    if(!e.ke||!e.mid){
        //for calendar plugin
        e.p=e.e.parents('[data-mid]'),
        e.ke=e.p.data('ke'),
        e.mid=e.p.data('mid'),
        e.file=e.p.data('file');
        e.auth=e.p.data('auth');
        e.status=e.p.data('status');
    }
    e.mon=$.ccio.mon[e.ke+e.mid+e.auth];
    switch(e.a){
        case'launch':
            e.preventDefault();
            e.href=$(this).attr('href'),
            e.e=$('#video_viewer');
            e.e.find('.modal-title span').html(e.mon.name+' - '+e.file)
            e.e.find('.modal-body').html('<video class="video_video" video="'+e.href+'" autoplay loop controls><source src="'+e.href+'" type="video/'+e.mon.ext+'"></video>')
            e.e.attr('mid',e.mid);
            e.f=e.e.find('.modal-footer');
            e.f.find('.download_link').attr('href',e.href).attr('download',e.file);
            e.f.find('[monitor="download"][host="dropbox"]').attr('href',e.href);
            e.e.modal('show')
                .attr('ke',e.ke)
                .attr('mid',e.mid)
                .attr('auth',e.auth)
                .attr('file',e.file);
            if(e.status==1){
                $.get(e.href.split('?')[0]+'/status/2',function(d){
                })
            }
        break;
        case'delete':
            e.href=e.p.find('[download]').attr('href')
            if(!e.href||e.href===''){
                e.href=e.p.attr('href')
            }
            $.confirm.e.modal('show');
            $.confirm.title.text('<%-cleanLang(lang['Delete Video'])%> : '+e.file)
            e.html='<%-cleanLang(lang.DeleteVideoMsg)%>'
            e.html+='<video class="video_video" autoplay loop controls><source src="'+e.href+'" type="video/'+e.mon.ext+'"></video>';
            $.confirm.body.html(e.html)
            $.confirm.click({title:'Delete Video',class:'btn-danger'},function(){
                $.getJSON($.ccio.init('location',$.users[e.auth])+e.auth+'/videos/'+e.ke+'/'+e.mid+'/'+e.file+'/delete',function(d){
                    $.ccio.log(d)
                })
            });
        break;
        case'download':
            e.preventDefault();
            switch(e.e.attr('host')){
                    <% if(config.DropboxAppKey){ %>
                case'dropbox':
                    Dropbox.save(e.e.attr('href'),e.e.attr('download'),{progress: function (progress) {$.ccio.log(progress)},success: function () {
                        $.ccio.log("<%-lang.dropBoxSuccess%>");
                    }});
                break;
                    <% } %>
            }
        break;
    }
})
.on('change','[localStorage]',function(e){
    e.e=$(this)
    e.localStorage=e.e.attr('localStorage')
    //pre-event
    switch(e.localStorage){
        case'montage':
            if($('#monitors_live').hasClass('montage')){
                e.montageClick=$('[system="montage"]').first();
                e.montageClick.click()
            }
        break;
    }
    e.value=e.e.val()
    $.ccio.op(e.localStorage,e.value)
    //finish event
    switch(e.localStorage){
        case'montage':
            if(e.montageClick){
                $.ccio.init('montage');
                setTimeout(function(){
                    e.montageClick.click()
                },500)
            }
        break;
    }
})
.on('click','[system]',function(e){
  var e={}; 
    e.e=$(this),
    e.a=e.e.attr('system');//the function
    switch(e.a){
        case'montage':
            e.startup=$.ccio.op().startup
            if(!e.startup){e.startup={}}
            e.container=$('#monitors_live').toggleClass('montage')
            if(!e.container.hasClass('montage')){
                e.startup.montage="0"
            }else{
                e.startup.montage=1
            }
            $.ccio.init('montage')
            $.ccio.op('startup',e.startup)
        break;
        case'switch':
            e.switch=e.e.attr('switch');
            e.o=$.ccio.op().switches
            if(!e.o){
                e.o={}
            }
            if(!e.o[e.switch]){
                e.o[e.switch]=0
            }
            if(e.o[e.switch]===1){
                e.o[e.switch]=0
            }else{
                e.o[e.switch]=1
            }
            $.ccio.op('switches',e.o)
            switch(e.switch){
                case'monitorOrder':
                    $.ccio.init('monitorOrder',{no:['#monitors_list .link-monitors-list[auth="'+$user.auth_token+'"][ke="'+$user.ke+'"]']},$user)
                    if($user.details.links){
                        $.each($user.details.links,function(n,v){
                            $.ccio.init('monitorOrder',{no:['#monitors_list .link-monitors-list[auth="'+v.auth_token+'"][ke="'+v.ke+'"]']},v)
                        })
                    }
                break;
            }
            switch(e.e.attr('type')){
                case'text':
                    if(e.o[e.switch]===1){
                        e.e.addClass('text-success')
                    }else{
                        e.e.removeClass('text-success')
                    }
                break;
            }
        break;
        case'cronStop':
            $.ccio.cx({f:'cron',ff:'stop'})
        break;
        case'cronRestart':
            $.ccio.cx({f:'cron',ff:'restart'})
        break;
        case'jpegToggle':
            e.cx={f:'monitor',ff:'jpeg_on'};
            if($.ccio.op().jpeg_on===true){
                e.cx.ff='jpeg_off';
            }
            $.ccio.cx(e.cx)
        break;
    }
})
.on('click','[class_toggle]',function(e){
    e.e=$(this);
    e.n=e.e.attr('data-target');
    e.v=e.e.attr('class_toggle');
    e.o=$.ccio.op().class_toggle;
    if($(e.n).hasClass(e.v)){e.t=0}else{e.t=1}
    if(!e.o)e.o={};
    e.o[e.n]=[e.v,e.t];
    $.ccio.op('class_toggle',e.o)
    $(e.n).toggleClass(e.v);
})
.on('change','[dropdown_toggle]',function(e){
    e.e=$(this);
    e.n=e.e.attr('dropdown_toggle');
    e.v=e.e.val();
    e.o=$.ccio.op().dropdown_toggle;
    if(!e.o)e.o={};
    e.o[e.n]=e.v;
    $.ccio.op('dropdown_toggle',e.o)
})
//monitor functions
.on('click','[monitor]',function(){
  var e={}; 
    e.e=$(this),
        e.a=e.e.attr('monitor'),//the function
        e.p=e.e.parents('[mid]'),//the parent element for monitor item
        e.ke=e.p.attr('ke'),//group key
        e.mid=e.p.attr('mid'),//monitor id
        e.auth=e.p.attr('auth'),//authkey
        e.mon=$.ccio.mon[e.ke+e.mid+e.auth];//monitor configuration
        var user
        if($.users[e.auth]){user=$.users[e.auth]}else{user=$user}
        if(!user){
            user=$user
        }
    switch(e.a){
        case'motion':
            if(!e.mon.motionDetectionRunning){
                $.ccio.init('streamMotionDetectOn',e,user)
            }else{
                $.ccio.init('streamMotionDetectOff',e,user)
            }
        break;
        case'pop':
            e.fin=function(img){
                if($.ccio.mon[e.ke+e.mid+user.auth_token].popOut){
                    $.ccio.mon[e.ke+e.mid+user.auth_token].popOut.close()
                }
                $.ccio.mon[e.ke+e.mid+user.auth_token].popOut = window.open($.ccio.init('location',user)+user.auth_token+'/embed/'+e.ke+'/'+e.mid+'/fullscreen|jquery|relative|gui','pop_'+e.mid+user.auth_token,'height='+img.height+',width='+img.width);
            }
            if(e.mon.watch===1){
                $.ccio.snapshot(e,function(url){
                    $('#temp').html('<img>')
                    var img=$('#temp img')[0]
                    img.onload=function(){
                        e.fin(img)
                    }
                    img.src=url
                })
            }else{
                var img={height:720,width:1280}
                e.fin(img)
            }
        break;
        case'mode':
            e.mode=e.e.attr('mode')
            if(e.mode){
                $.getJSON($.ccio.init('location',user)+user.auth_token+'/monitor/'+e.ke+'/'+e.mid+'/'+e.mode,function(d){
                    $.ccio.log(d)
                })
            }
        break;
        case'timelapse':
            $.timelapse.e.modal('show')
            $.timelapse.monitors.find('.monitor').remove()
            $.each($.ccio.mon,function(n,v){
                $.timelapse.monitors.append('<option class="monitor" value="'+v.mid+'">'+v.name+'</option>')
            })
            e.e=$.timelapse.monitors.find('.monitor').prop('selected',false)
            if(e.mid!==''){
                e.e=$.timelapse.monitors.find('.monitor[value="'+e.mid+'"]')
            }
            e.e.first().prop('selected',true)
            $.timelapse.f.submit()
        break;
        case'powerview':
            $.pwrvid.e.modal('show')
            $.pwrvid.m.empty()
            $.each($.ccio.mon,function(n,v){
                $.pwrvid.m.append('<option value="'+v.mid+'">'+v.name+'</option>')
            })
            e.e=$.pwrvid.m.find('option').prop('selected',false)
            if(e.mid!==''){
                e.e=$.pwrvid.m.find('[value="'+e.mid+'"]')
            }
            e.e.first().prop('selected',true)
            $.pwrvid.f.submit()
        break;
        case'region':
            if(!e.mon){
                $.ccio.init('note',{title:'<%-cleanLang(lang['Unable to Launch'])%>',text:'<%-cleanLang(lang.UnabletoLaunchText)%>',type:'error'});
                return;
            }
            e.d=JSON.parse(e.mon.details);
            e.width=$.aM.e.find('[detail="detector_scale_x"]');
            e.height=$.aM.e.find('[detail="detector_scale_y"]');
            e.d.cords=$.aM.e.find('[detail="cords"]').val();
            if(e.width.val()===''){
                e.d.detector_scale_x=320;
                e.d.detector_scale_y=240;
                $.aM.e.find('[detail="detector_scale_x"]').val(e.d.detector_scale_x);
                $.aM.e.find('[detail="detector_scale_y"]').val(e.d.detector_scale_y);
            }else{
                e.d.detector_scale_x=e.width.val();
                e.d.detector_scale_y=e.height.val();
            }
            
            $.zO.e.modal('show');
            $.zO.o().attr('width',e.d.detector_scale_x).attr('height',e.d.detector_scale_y);
            $.zO.c.css({width:e.d.detector_scale_x,height:e.d.detector_scale_y});
                if(e.d.cords&&(e.d.cords instanceof Object)===false){
                try{e.d.cords=JSON.parse(e.d.cords);}catch(er){}
            }
            if(!e.d.cords||e.d.cords===''){
                e.d.cords={
                    red:{ name:"red",sensitivity:0.0005, points:[[0,0],[0,100],[100,0]] },
                }
            }
            $.zO.regionViewerDetails=e.d;
            $.zO.initRegionList()
        break;
        case'snapshot':
            $.ccio.snapshot(e,function(url){
                $('#temp').html('<a href="'+url+'" download="'+$.ccio.init('tf')+'_'+e.ke+'_'+e.mid+'.jpg">a</a>').find('a')[0].click();
            });
        break;
        case'control':
            e.a=e.e.attr('control'),e.j=JSON.parse(e.mon.details);
            $.ccio.cx({f:'monitor',ff:'control',direction:e.a,mid:e.mid,ke:e.ke},user)
        break;
        case'videos_table':case'calendar'://call videos table or calendar
            $.vidview.launcher=$(this);
            e.limit=$.vidview.limit.val();
            if(!$.vidview.current_mid||$.vidview.current_mid!==e.mid){
                $.vidview.current_mid=e.mid
                $.vidview.current_page=1;
                if(e.limit.replace(/ /g,'')===''){
                    e.limit='100';
                }
                if(e.limit.indexOf(',')===-1){
                    e.limit='0,'+e.limit
                }else{
                    e.limit='0,'+e.limit.split(',')[1]
                }
                if(e.limit=='0,0'){
                    e.limit='0'
                }
                $.vidview.limit.val(e.limit)
            }
            e.dateRange=$('#videos_viewer_daterange').data('daterangepicker');
            e.videoURL=$.ccio.init('location',user)+user.auth_token+'/videos/'+e.ke+'/'+e.mid+'?limit='+e.limit+'&start='+$.ccio.init('th',e.dateRange.startDate)+'&end='+$.ccio.init('th',e.dateRange.endDate);
            $.getJSON(e.videoURL,function(d){
                d.pages=d.total/100;
                $('.video_viewer_total').text(d.total)
                if(d.pages+''.indexOf('.')>-1){++d.pages}
                $.vidview.page_count=d.pages;
                d.count=1
                $.vidview.pages.empty()
                d.fn=function(drawOne){
                    if(d.count<=$.vidview.page_count){
                        $.vidview.pages.append('<a class="btn btn-primary" page="'+d.count+'">'+d.count+'</a> ')
                        ++d.count;
                        d.fn()
                    }
                }
                d.fn()
                $.vidview.pages.find('[page="'+$.vidview.current_page+'"]').addClass('active')
                e.v=$.vidview.e;
                e.b=e.v.modal('show').find('.modal-body .contents');
                e.t=e.v.find('.modal-title i');
                switch(e.a){
                    case'calendar':
                       e.t.attr('class','fa fa-calendar')
                       e.ar=[];
                        if(d.videos[0]){
                            $.each(d.videos,function(n,v){
                                if(v.status!==0){
                                    var n=$.ccio.mon[v.ke+v.mid+user.auth_token];
                                    if(n){v.title=n.name+' - '+(parseInt(v.size)/1000000).toFixed(2)+'mb';}
                                    v.start=v.time;
                                    v.filename=$.ccio.init('tf',v.time)+'.'+v.ext;
                                    e.ar.push(v);
                                }
                            })
                            e.b.html('')
                            try{e.b.fullCalendar('destroy')}catch(er){}
                            e.b.fullCalendar({
                                header: {
                                    left: 'prev,next today',
                                    center: 'title',
                                    right: 'month,agendaWeek,agendaDay,listWeek'
                                },
                                defaultDate: moment(d.videos[0].time).format('YYYY-MM-DD'),
                                navLinks: true,
                                eventLimit: true,
                                events:e.ar,
                                eventClick:function(f){
                                    $('#temp').html('<div mid="'+f.mid+'" ke="'+f.ke+'" auth="'+user.auth_token+'" file="'+f.filename+'"><div video="launch" href="'+f.href+'"></div></div>').find('[video="launch"]').click();
                                    $(this).css('border-color', 'red');
                                }
                            });
                            setTimeout(function(){e.b.fullCalendar('changeView','month');e.b.find('.fc-scroller').css('height','auto')},500)
                        }else{
                            e.b.html('<div class="text-center"><%-cleanLang(lang.NoVideosFoundForDateRange)%></div>')
                        }
                    break;
                    case'videos_table':
                        e.t.attr('class','fa fa-film')
                        e.tmp='<table class="table table-striped" style="max-height:500px">';
                        e.tmp+='<thead>';
                        e.tmp+='<tr>';
                        e.tmp+='<th><div class="checkbox"><input id="videos_select_all" type="checkbox"><label for="videos_select_all"></label></div></th>';
                        e.tmp+='<th data-field="Closed" data-sortable="true"><%-cleanLang(lang.Closed)%></th>';
                        e.tmp+='<th data-field="Ended" data-sortable="true"><%-cleanLang(lang.Ended)%></th>';
                        e.tmp+='<th data-field="Started" data-sortable="true"><%-cleanLang(lang.Started)%></th>';
                        e.tmp+='<th data-field="Monitor" data-sortable="true"><%-cleanLang(lang.Monitor)%></th>';
                        e.tmp+='<th data-field="Filename" data-sortable="true"><%-cleanLang(lang.Filename)%></th>';
                        e.tmp+='<th data-field="Size" data-sortable="true"><%-cleanLang(lang['Size (mb)'])%></th>';
                        e.tmp+='<th data-field="Preview" data-sortable="true"><%-cleanLang(lang.Preview)%></th>';
                        e.tmp+='<th data-field="Watch" data-sortable="true"><%-cleanLang(lang.Watch)%></th>';
                        e.tmp+='<th data-field="Download" data-sortable="true"><%-cleanLang(lang.Download)%></th>';
                        e.tmp+='<th class="permission_video_delete" data-field="Delete" data-sortable="true"><%-cleanLang(lang.Delete)%></th>';
//                        e.tmp+='<th class="permission_video_delete" data-field="Fix" data-sortable="true"><%-cleanLang(lang.Fix)%></th>';
                        e.tmp+='</tr>';
                        e.tmp+='</thead>';
                        e.tmp+='<tbody>';
                        $.each(d.videos,function(n,v){
                            if(v.status!==0){
                                if(user!==$user&&v.href.charAt(0)==='/'){
                                    v.href=$.ccio.init('location',user)+(v.href.substring(1))
                                }
                                v.mon=$.ccio.mon[v.ke+v.mid+user.auth_token];
                                v.start=v.time;
                                v.filename=$.ccio.init('tf',v.time)+'.'+v.ext;
                                e.tmp+='<tr data-ke="'+v.ke+'" data-status="'+v.status+'" data-mid="'+v.mid+'" data-file="'+v.filename+'" data-auth="'+v.mon.user.auth_token+'">';
                                e.tmp+='<td><div class="checkbox"><input id="'+v.ke+'_'+v.filename+'" name="'+v.filename+'" value="'+v.mid+'" type="checkbox"><label for="'+v.ke+'_'+v.filename+'"></label></div></td>';
                                e.tmp+='<td><span class="livestamp" title="'+v.end+'"></span></td>';
                                e.tmp+='<td title="'+v.end+'">'+moment(v.end).format('h:mm:ss A, MMMM Do YYYY')+'</td>';
                                e.tmp+='<td title="'+v.time+'">'+moment(v.time).format('h:mm:ss A, MMMM Do YYYY')+'</td>';
                                e.tmp+='<td>'+v.mon.name+'</td>';
                                e.tmp+='<td>'+v.filename+'</td>';
                                e.tmp+='<td>'+(parseInt(v.size)/1000000).toFixed(2)+'</td>';
                                e.tmp+='<td><a class="btn btn-sm btn-default preview" href="'+v.href+'">&nbsp;<i class="fa fa-play-circle"></i>&nbsp;</a></td>';
                                e.tmp+='<td><a class="btn btn-sm btn-primary" video="launch" href="'+v.href+'">&nbsp;<i class="fa fa-play-circle"></i>&nbsp;</a></td>';
                                e.tmp+='<td><a class="btn btn-sm btn-success" download="'+v.mid+'-'+v.filename+'" href="'+v.href+'?downloadName='+v.mid+'-'+v.filename+'">&nbsp;<i class="fa fa-download"></i>&nbsp;</a></td>';
                                e.tmp+='<td class="permission_video_delete"><a class="btn btn-sm btn-danger" video="delete">&nbsp;<i class="fa fa-trash"></i>&nbsp;</a></td>';
//                                e.tmp+='<td class="permission_video_delete"><a class="btn btn-sm btn-warning" video="fix">&nbsp;<i class="fa fa-wrench"></i>&nbsp;</a></td>';
                                e.tmp+='</tr>';
                            }
                        })
                        e.tmp+='</tbody>';
                        e.tmp+='</table>';
                        e.b.html(e.tmp);delete(e.tmp)
                        $.ccio.init('ls');
                        $.vidview.e.find('table').bootstrapTable();
                    break;
                }
            })
        break;
        case'fullscreen':
            e.e=e.e.parents('.monitor_item');
            e.e.addClass('fullscreen')
            e.vid=e.e.find('.stream-element')
            if(e.vid.is('canvas')){
                e.doc=$('body')
               e.vid.attr('height',e.doc.height())
               e.vid.attr('width',e.doc.width())
            }
            $.ccio.init('fullscreen',e.vid[0])
        break;
        case'watch_on':
            $.ccio.cx({f:'monitor',ff:'watch_on',id:e.mid},user)
        break;
        case'control_toggle':
            e.e=e.p.find('.PTZ_controls');
            if(e.e.length>0){e.e.remove()}else{e.p.append('<div class="PTZ_controls"><div class="pad"><div class="control top" monitor="control" control="up"></div><div class="control left" monitor="control" control="left"></div><div class="control right" monitor="control" control="right"></div><div class="control bottom" monitor="control" control="down"></div><div class="control middle" monitor="control" control="center"></div></div><div class="btn-group btn-group-sm btn-group-justified"><a title="<%-cleanLang(lang['Zoom In'])%>" class="zoom_in btn btn-default" monitor="control" control="zoom_in"><i class="fa fa-search-plus"></i></a><a title="<%-cleanLang(lang['Zoom Out'])%>" class="zoom_out btn btn-default" monitor="control" control="zoom_out"><i class="fa fa-search-minus"></i></a></div><div class="btn-group btn-group-sm btn-group-justified"><a title="<%-cleanLang(lang['Enable Nightvision'])%>" class="nv_enable btn btn-default" monitor="control" control="enable_nv"><i class="fa fa-moon-o"></i></a><a title="<%-cleanLang(lang['Disable Nightvision'])%>" class="nv_disable btn btn-default" monitor="control" control="disable_nv"><i class="fa fa-sun-o"></i></a></div></div>')}
        break;
        case'watch':
            if($("#monitor_live_"+e.mid+user.auth_token).length===0||$.ccio.mon[e.ke+e.mid+user.auth_token].watch!==1){
                $.ccio.cx({f:'monitor',ff:'watch_on',id:e.mid},user)
            }else{
                $("#main_canvas").animate({scrollTop:$("#monitor_live_"+e.mid+user.auth_token).offset().top-($('#main_header').height()+10)},500);
            }
        break;
        case'watch_off':
            $.ccio.cx({f:'monitor',ff:'watch_off',id:e.mid},user)
        break;
        case'delete':
            e.m=$('#confirm_window').modal('show');e.f=e.e.attr('file');
            $.confirm.title.text('<%-cleanLang(lang['Delete Monitor'])%> : '+e.mon.name)
            e.html='<%-cleanLang(lang.DeleteMonitorText)%>'
            e.html+='<table class="info-table"><tr>';
            $.each(e.mon,function(n,v,g){
                if(n==='host'&&v.indexOf('@')>-1){g=v.split('@')[1]}else{g=v};
                try{JSON.parse(g);return}catch(err){}
                e.html+='<tr><td>'+n+'</td><td>'+g+'</td></tr>';
            })
            e.html+='</tr></table>';
            $.confirm.body.html(e.html)
            $.confirm.click({title:'Delete Monitor',class:'btn-danger'},function(){
                $.get($.ccio.init('location',user)+user.auth_token+'/configureMonitor/'+user.ke+'/'+e.mon.mid+'/delete',function(d){
                    $.ccio.log(d)
                })
            });
        break;
        case'edit':
            e.p=$('#add_monitor'),e.mt=e.p.find('.modal-title')
            e.p.find('.am_notice').hide()
            e.p.find('[detailcontainer="detector_cascades"]').prop('checked',false).parents('.mdl-js-switch').removeClass('is-checked')
            if(!$.ccio.mon[e.ke+e.mid+user.auth_token]){
                e.p.find('.am_notice_new').show()
                //new monitor
                e.p.find('[monitor="delete"]').hide()
                e.mt.find('span').text('Add'),e.mt.find('i').attr('class','fa fa-plus');
                //default values
                e.values=$.aM.generateDefaultMonitorSettings();
            }else{
                e.p.find('.am_notice_edit').show()
                //edit monitor
                e.p.find('[monitor="delete"]').show()
                e.mt.find('span').text('<%-cleanLang(lang.Edit)%>');
                e.mt.find('i').attr('class','fa fa-wrench');
                e.values=$.ccio.mon[e.ke+e.mid+user.auth_token];
            }
            $.aM.selected=e.values;
//            e.openTabs=$.ccio.op().tabsOpen
//            if(e.openTabs[e.mid]){
//                e.values=e.openTabs[e.mid]
//            }
            $.aM.import(e)
            $('#add_monitor').modal('show')
        break;
    }
})

$('.modal').on('hidden.bs.modal',function(){
    $(this).find('video').remove();
    $(this).find('iframe').attr('src','about:blank');
});
$('.modal').on('shown.bs.modal',function(){
    e={e:$(this).find('.flex-container-modal-body')}
    if(e.e.length>0){
        e.e.resize()
    }
});

$('body')
.on('click','.scrollTo',function(ee){
    ee.preventDefault()
    var e = {e:$(this)};
    e.parent=e.e.attr('scrollToParent')
    if(!e.parent){
        e.parent='body,html'
    }
    $(e.parent).animate({
        scrollTop: $(e.e.attr('href')).position().top
    }, 400);
})
.on('resize','.flex-container-modal-body',function(e){
    e=$(this)
    e.find('.flex-modal-block').css('height',e.height())
})
.on('resize','#monitors_live .monitor_item',function(e){
    e.e=$(this).find('.mdl-card__media');
    e.c=e.e.find('canvas');
    e.c.attr('height',e.e.height());
    e.c.attr('width',e.e.width());
})
.on('keyup','.search-parent .search-controller',function(){
    _this = this;
    $.each($(".search-parent .search-body .search-row"), function() {
        if($(this).text().toLowerCase().indexOf($(_this).val().toLowerCase()) === -1)
           $(this).hide();
        else
           $(this).show();
    });
})
.on('dblclick','.stream-hud',function(){
    $(this).parents('[mid]').find('[monitor="fullscreen"]').click();
})
//.on('mousemove',".magnifyStream",$.ccio.magnifyStream)
//.on('touchmove',".magnifyStream",$.ccio.magnifyStream);
    //check switch UI
    e.o=$.ccio.op().switches;
    if(e.o){
        $.each(e.o,function(n,v){
            $('[system="switch"][switch="'+n+'"]').each(function(m,b){
                b=$(b);
                switch(b.attr('type')){
                    case'text':
                    if(v===1){
                        b.addClass('text-success')
                    }else{
                        b.removeClass('text-success')
                    }
                    break;
                 }
            })
        })
    }
    //set class toggle preferences
    e.o=$.ccio.op().class_toggle;
    if(e.o){
        $.each(e.o,function(n,v){
            if(v[1]===1){
                $(n).addClass(v[0])
            }else{
                $(n).removeClass(v[0])
            }
        })
    }
    //set dropdown toggle preferences
    e.o=$.ccio.op().dropdown_toggle;
    if(e.o){
        $.each(e.o,function(n,v){
            $('[dropdown_toggle="'+n+'"]').val(v).change()
        })
    }
    //set startup preferences
    e.o=$.ccio.op().startup;
    if(e.o){
        $.each(e.o,function(n,v){
            switch(n){
                case'montage':
                    if(v===1){
                        $('#monitors_live').addClass('montage')
                        $.ccio.init('montage')
                    }
                break;
            }
        })
    }
    //set localStorage input values
    e.o=$.ccio.op();
    if(e.o){
        $.each(e.o,function(n,v){
            if(typeof v==='string'){
                $('[localStorage="'+n+'"]').val(v)
            }
        })
    }
})
document.addEventListener("fullscreenchange", onFullScreenChange, false);
document.addEventListener("webkitfullscreenchange", onFullScreenChange, false);
document.addEventListener("mozfullscreenchange", onFullScreenChange, false);
function onFullScreenChange() {
    var fullscreenElement = document.fullscreenElement || document.mozFullScreenElement || document.webkitFullscreenElement;
    if(!fullscreenElement){
        $('.fullscreen').removeClass('fullscreen')
        setTimeout(function(){
            $('canvas.stream-element').resize();
        },2000)
    }
}