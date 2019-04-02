var fs = require('fs');
var os = require('os');
var DDPClient = require("ddp");
WebSocket = require('ws');
var login = require('ddp-login');
var CryptoJS = require("crypto-js");
var Docker = require('dockerode');
var YAML = require('yamljs');
var fs = require("fs");
var http = require("http");
var StringDecoder = require('string_decoder').StringDecoder;
var docker = new Docker();
var flowerws = process.env.FLOWER_WS || 'ws://flower:5555/api/task/events/task-succeeded/';
var exec = require('child_process').exec;

const hostname = '127.0.0.1';
const port = 3380;

const http_server = http.createServer(function(req, res) {
  if (req.method === 'POST') {
    const decoder = new StringDecoder('utf-8');
    var payload = '';

    req.on('data', (data) => {
      payload += decoder.write(data);
    });

    req.on('end', () => {
      payload += decoder.end();

      // Parse payload to object.
      payload = JSON.parse(payload);

      console.log('req url: ' + req.url);
      console.log('payload: ' + JSON.stringify(payload));

      // Do smoething with the payload....
      //if (req.url == '/api/login')
      res.statusCode = 200;
      res.setHeader('Content-Type', 'application/json');
      res.end(JSON.stringify({result: 'success'}));
    });
  }
});

var ddpClient = new DDPClient({
  // All properties optional, defaults shown
  host : process.env.HOST_ADDRESS || "192.168.0.7",
  port : process.env.HOST_PORT || 3000,
  ssl  : false,
  maintainCollections : true,
  ddpVersion : '1'
});

var DEVICE_UUID_FILE = process.env.UUID_FILE || '/dev/ro_serialno'
var DEVICE_GROUP_ID = '/data/data/com.termux/files/home/.groupid.txt'
var VERSION_FILE = process.env.VERSION_FILE || '../version'
var AUTO_UPDATE_FILE = process.env.AUTO_UPDATE_FILE || '../workaipython/wtconf/enableWT'
var DOCKER_COMPOSE_YML = process.env.DOCKER_COMPOSE_YML || '../docker-compose.yml'
var RUNTIME_DIR = process.env.RUNTIME_DIR || '../'
var RESTART_TIMEOUT = process.env.RESTART_TIMEOUT || 10
var DOCKER_COMPOSE_YML_FILENAME = process.env.DOCKER_COMPOSE_YML_FILENAME || 'docker-compose.yml'
var DOCKER_SOCK = '/var/run/docker.sock'

function get_device_uuid(cb){
  fs.readFile(DEVICE_UUID_FILE, function (err,data) {
    if (err) {
      return cb && cb('no_uuid')
    }
    return cb && cb(data.toString().replace(/(\r\n\t|\n|\r\t)/gm,""))
  });
}

var connectedToServer = false
var timesInSilence = 0
function login_with_device_id(device_id, callback){
  var real_pwd = CryptoJS.HmacSHA256(device_id, "sharp_ai98&#").toString()
  console.log(real_pwd)
  login(ddpClient,
    {  // Options below are the defaults
       env: 'METEOR_TOKEN',  // Name of an environment variable to check for a
                             // token. If a token is found and is good,
                             // authentication will require no user interaction.
       method: 'username',    // Login method: account, email, username or token
       account: device_id,        // Prompt for account info by default
       pass: real_pwd,           // Prompt for password by default
       retry: 5,             // Number of login attempts to make
       plaintext: false      // Do not fallback to plaintext password compatibility
                             // for older non-bcrypt accounts
    },
    function (error, userInfo) {
      if (error) {
        // Something went wrong...
        console.log('login error')
      } else {
        // We are now logged in, with userInfo.token as our session auth token.
        token = userInfo.token;
        console.log('login ok:'+token)
        sub_command_list(device_id)
        sub_device_info(device_id)
      }

      callback && callback(error,userInfo)
    }
  );
}
function connectToMeteorServer(device_id){
  ddpClient.connect(function(error, wasReconnect) {
    // If autoReconnect is true, this callback will be invoked each time
    // a server connection is re-established
    if (error) {
      console.log('DDP connection error!');
      process.exit(-10)
      return;
    }
    if (wasReconnect) {
      console.log('Reestablishment of a connection. The status is hard to keep,just restart');

      process.exit(10)
      /*connectedToServer = true
      login_with_device_id(device_id,function(error,userInfo){
        if(error){
          console.log(error)
        }
      })*/
    } else {
      console.log('new connection to meteor server')
      connectedToServer = true
      login_with_device_id(device_id,function(error,userInfo){
        if(error){
          console.log(error)
        }
      })
    }
  })
}

function processing_command_config(config, cb) {
    if(!config)
        return cb && cb("invalied args");

    var autoUpdate = config.autoUpdate;
    var update_enabled = fs.existsSync(AUTO_UPDATE_FILE);
    /*going to enable update*/
    if(autoUpdate == true) {
        fs.writeFile(AUTO_UPDATE_FILE, "enable", function(err) {
            if(err) {
                return cb && cb("fs.writeFile failed");
            }
            else {
                console.log("watchtower enabled")
                return cb && cb ();
            }
        });
    }
    /*going to disable update*/
    else {
        if(!update_enabled) {
            console.log("watchtower disabled")
            return cb && cb ();
        }
        fs.unlink(AUTO_UPDATE_FILE, function(err){
            if(err){
                return cb && cb(err)
            }
            else {
                console.log("watchtower disabled")
                return cb && cb ();
            }
        })
    }
}

function processing_command_done(id, client_id) {
    console.log('command done')
    ddpClient.call('cmd_done',[id, {"client_id": client_id, "command_id": id}])
}

function processing_command(id, client_id){
  var command_contex = ddpClient.collections.commands[id];
  var clientid = command_contex.client_id;
  var cmd = command_contex.command;

  if(cmd && cmd == "config") {
      console.log("sync config to local")
      if(command_contex.config) {
          processing_command_config(command_contex.config, function(err) {
              processing_command_done(id, clientid);
          })
      }
      else {
          processing_command_done(id, clientid);
      }
  } else if(cmd && cmd == "restartmonit") {
      if(clientid == client_id) {
          processing_command_done(id, clientid);
          console.log("got cmd: restartmonit, goingto restart in 5sec")
          setTimeout(function() {
              process.exit(-10)
          },5000)
      }
  } else {
      processing_command_done(id, clientid);
  }
}

function handle_group_id(group_id){
  console.log('yes, my group id is ['+ group_id +'] for now')

  fs.writeFile(DEVICE_GROUP_ID, group_id, function(err) {
      if(err) {
          return console.log(err);
      }

      console.log("The file was saved!");
  });
}
function sub_device_info(client_id){
      /*
       * Observe a collection.
       */
      var observer = ddpClient.observe("devices");
      observer.added = function(id) {
        console.log("[ADDED] to " + observer.name + ":  " + id);
        console.log(ddpClient.collections.devices);
        if(ddpClient.collections.devices[id]){
          var doc = ddpClient.collections.devices[id];
          if(doc && doc['groupId']){
              handle_group_id(doc['groupId'])
          }
        }
        if(doc && doc.hasOwnProperty('autoUpdate')) {
            processing_command_config({'autoUpdate': doc['autoUpdate']}, function(err) {
                if(err) console.log(err);
            })
        }
        else {
            console.log("autoUpdate not found")
            processing_command_config({'autoUpdate': false}, function(err) {
                if(err) console.log(err);
            })
        }
      };
      observer.changed = function(id, oldFields, clearedFields, newFields) {
        console.log("[CHANGED] in " + observer.name + ":  " + id);
        console.log("[CHANGED] old field values: ", oldFields);
        console.log("[CHANGED] cleared fields: ", clearedFields);
        console.log("[CHANGED] new fields: ", newFields);
        if(newFields['groupId']){
          handle_group_id(newFields['groupId'])
        }

        if(clearedFields && clearedFields.hasOwnProperty('autoUpdate')) {
            console.log('cleared autoUpdate')
            processing_command_config({'autoUpdate': false}, function(err) {
                if(err) {
                    console.log(err);
                }
            })
        }
        if(newFields && newFields.hasOwnProperty('autoUpdate')) {
            processing_command_config({'autoUpdate': newFields['autoUpdate']}, function(err) {
                if(err) {
                    console.log(err);
                }
            })
        }
      };
      observer.removed = function(id, oldValue) {
        console.log("[REMOVED] in " + observer.name + ":  " + id);
        console.log("[REMOVED] previous value: ", oldValue);
      };

      /*
       * Subscribe to a Meteor Collection
       */
      ddpClient.subscribe(
        'devices-by-uuid',                  // name of Meteor Publish function to subscribe to
        [client_id],                       // any parameters used by the Publish function
        function () {             // callback when the subscription is complete
          console.log('commands complete:');
          console.log(ddpClient.collections.devices);
        }
      );
}
function sub_command_list(client_id){
      /*
     * Observe a collection.
     */
    var observer = ddpClient.observe("commands");
    observer.added = function(id) {
      console.log("[ADDED] to " + observer.name + ":  " + id);
      console.log(ddpClient.collections.commands);
      processing_command(id, client_id)
    };
    observer.changed = function(id, oldFields, clearedFields, newFields) {
      console.log("[CHANGED] in " + observer.name + ":  " + id);
      console.log("[CHANGED] old field values: ", oldFields);
      console.log("[CHANGED] cleared fields: ", clearedFields);
      console.log("[CHANGED] new fields: ", newFields);
    };
    observer.removed = function(id, oldValue) {
      console.log("[REMOVED] in " + observer.name + ":  " + id);
      console.log("[REMOVED] previous value: ", oldValue);
    };

    /*
     * Subscribe to a Meteor Collection
     */
    ddpClient.subscribe(
      'commands',                  // name of Meteor Publish function to subscribe to
      [client_id],                       // any parameters used by the Publish function
      function () {             // callback when the subscription is complete
        console.log('commands complete:');
        console.log(ddpClient.collections.commands);
      }
    );
}

function cpu_mem_uptime_temp(cb) {
    var cpu_average = 0;
    var mem = {'free': -1, 'total':-1, 'usage': 0};
    var uptime = os.uptime();
    var temp = {'cpu': -1, 'gpu': -1};

    /*CPU*/
    var cpus = os.cpus();
    if(typeof cpus === 'undefined'){
      cpu_average = 'N/A';
    } else {
      for(var i=0;i<cpus.length;i++) {
          var cpu = cpus[i];
          var usage = 0;
          if (cpu && cpu.times) {
            var total = 1;
            var idle = 0;
            total = cpu.times.user + cpu.times. user+ cpu.times.nice + cpu.times.sys + cpu.times.idle + cpu.times.irq;
            idle = cpu.times.idle;
            usage = (1 - (idle/total)).toFixed(2);
          }
          cpu_average += Number(usage);
      }
      cpu_average = (cpu_average/cpus.length).toFixed(2);
    }

    /*MEM*/
    mem.free = os.freemem();
    mem.total = os.totalmem();
    if(mem.total > 0 ) {
        mem.usage = (1 - (mem.free/mem.total)).toFixed(2);
    }

    /*TEMP*/
    for(var i=0;i<4;i++) {
        var dir = "/sys/class/thermal/thermal_zone" + i + '/';
        var type_file = dir + 'type';
        var temp_file = dir + 'temp';
        var exists = fs.existsSync(dir);
        if(!exists)
            continue;

        var typename = ''
        var temp_val = ''
        try {
            typename = fs.readFileSync(type_file, 'utf8').replace(/[\r\n]/g,"");
            temp_val = fs.readFileSync(temp_file, 'utf8').replace(/[\r\n]/g,"");
        }
        catch(err) {
            console.log("read TEMP failed ", err)
        }

        if(typename.length < 1 && temp_val.length < 1)
            continue;

        if(typename.startsWith("soc-thermal") || typename.startsWith("exynos-therm")) {
            temp.cpu = temp_val;
        } else if(typename.startsWith("gpu-thermal")) {
            temp.gpu = temp_val;
        }
    }

    return cb && cb({'cpu': cpu_average, 'mem': mem, 'uptime': uptime, 'temp': temp})
}

function get_docker_version(filepath, cb) {
    var exists = fs.existsSync(DOCKER_SOCK);
    var ymlexists = fs.existsSync(filepath);
    if(!exists || !ymlexists)
         return cb && cb("yml not found, or docker not install", null)
    var data = null;
    try{
        data = YAML.parse(fs.readFileSync(filepath).toString());
    }
    catch(e){
        console.log('error..');
    }
    if(!data || !data.services)
        return cb && cb("YAML.parse failed", null);
    var services = data.services;
    var imagesname = {};
    for (var prop in services) {
        if(prop && services[prop] && services[prop].image)
            imagesname[services[prop].image] = '????????????'
    }
    if(imagesname.length < 1)
        return cb && cb("image name not found", null);

   docker.listImages(function(err, list) {
     if (err) return cb && cb(err, null);
     var result = {};
     for(var prop in imagesname) {
         var shortname = prop.split('/')[1].split(':')[0]
         result[shortname] = imagesname[prop]

         for (var i = 0, len = list.length; i < len; i++) {
             if(!list[i].RepoTags || !list[i].Id)
                 continue

                 repotag = list[i].RepoTags;
                 for(var j = 0; j < repotag.length; j++) {
                     if(prop == repotag[j]) {
                         tag = list[i].Id.split(':')[1]
                         result[shortname] = tag.slice(0,11)
                     }
                 }
         }
     }
     return cb && cb(null, result);
   });
}

function get_curent_version(cb) {
    var all_version = {'v1': 'unknown', 'v2': 'unknown'};
    var exists = fs.existsSync(VERSION_FILE);
    if(exists) {
        var version_val = fs.readFileSync(VERSION_FILE, 'utf8').replace(/[\r\n]/g,"");
        if(version_val.length > 0) {
            all_version.v1 = version_val;
        }
    }
    /* get v2 from docker*/
    get_docker_version(DOCKER_COMPOSE_YML, function(err, result) {
        if(!err && result)
            all_version.v2 = result;

        return cb && cb(all_version);
    })
}

function get_curent_config(cb) {
    var all_config = {'autoupdate': false};
    var exists = fs.existsSync(AUTO_UPDATE_FILE);
    if(exists) {
        all_config.autoupdate = true;
    }
    return cb && cb(all_config);
}

var connected_to_camera = false;
var camera_monitor_timeout = null;
var status = {
    total_tasks:0,
    face_detected:0,
    face_recognized:0,
    heartbeats: 0,
    os: {},
    version: {},
    cfg: {}
}
function restart_docker_compose(){
    var exists = fs.existsSync(DOCKER_SOCK);
    if(!exists) {
        return;
    }
    var command = `cd ${RUNTIME_DIR} && docker-compose -f ${DOCKER_COMPOSE_YML_FILENAME} down && docker-compose -f ${DOCKER_COMPOSE_YML_FILENAME} up`
    console.log(command)
    exec(command, function(err, stdout, stderr) {
      if (err) {
        console.log(`stdout: ${stdout}`);
        console.log(`stderr: ${stderr}`);
        console.log("node couldn't execute the command")
        return;
      }

      // the *entire* stdout and stderr (buffered)
      console.log(`stdout: ${stdout}`);
      console.log(`stderr: ${stderr}`);
    });
}
function connectToFlower(){
  var ws = new WebSocket(flowerws);
  ws.onmessage = function (event) {
      var result = JSON.parse(event.data)
      status.total_tasks++;
      if(result.hostname == "celery@detect"){
         var detect_result = JSON.parse(result.result.replace(/\'/g,""))
         if(detect_result.detected == true){
           status.face_detected++;
           console.log('face detected')
         }
      } else if(result.hostname == "celery@embedding"){
         if(result.result.indexOf('embedding_str') > -1){
           console.log('embedded_v2')
           return
         }
      } else if(result.hostname == "celery@classify"){
         console.log('Classify Result')
         var extract_result = JSON.parse(result.result.replace(/\'/g,""))
         if(extract_result.result.recognized){
            status.face_recognized++;
            console.log('face recognized')
         }else{
            console.log('face not recognized')
         }
      }
  }
  ws.onerror = function(event) {
      console.log("ws.onerror ")
  };
  ws.onclose = function(event) {
      console.log("ws.onclose ")
      setTimeout(function(){
          connectToFlower()
      },5*1000)
  };
}
get_device_uuid(function(uuid){
  var my_client_id = uuid
  connectToMeteorServer(my_client_id)
  connectToFlower()

  http_server.listen(port, hostname, function() {
    console.log(`Server running at http://${hostname}:${port}/`);
  });

  setInterval(function(){
    cpu_mem_uptime_temp(function(os_info) {
        status.os = os_info;
    })

    /*get version every 10min*/
    if(status.heartbeats%9 == 0) {
        get_curent_version(function(version_info) {
           status.version = version_info;
        })
    }
    get_curent_config(function(cfg) {
       status.cfg = cfg;
    })


    ddpClient.call('report',[{
        clientID :my_client_id,
        total_tasks:     status.total_tasks,
        face_detected:   status.face_detected,
        face_recognized: status.face_recognized,
        os:              status.os,
        version:         status.version,
        cfg:             status.cfg }])

    if(status.total_tasks === 0){
        timesInSilence++
        if(timesInSilence >= RESTART_TIMEOUT){
            console.log('need restart docker compose')
            restart_docker_compose()
            timesInSilence = 0
        }
    } else {
        timesInSilence = 0
    }
    status.total_tasks = 0;
    status.face_detected = 0;
    status.face_recognized = 0;
    status.heartbeats += 1;
  },60*1000)
})
