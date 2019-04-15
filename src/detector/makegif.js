var fs = require('fs');
var path = require('path');
var Gm = require("gm"); //.subClass({ imageMagick: true });
var readdir = require('readdir-absolute');
var upload = require('./upload');
var REMOVE_IMG_UPLOADED = true;

function generateGif(type,dir,name_sorting,cb){
  readdir(dir,function(err,list){
    var files = list.filter(function(element) {
      var extName = path.extname(element);
      return extName === '.'+type;
    })
    if(name_sorting){
      files = files.sort(function(a, b) {
        var a_num = parseInt(/frame-(.*?).jpg/.exec(a.toString())[1])
        var b_num = parseInt(/frame-(.*?).jpg/.exec(b.toString())[1])
        return a_num - b_num
      });
    } else {
      files = files.sort(function(a, b) {
         return fs.statSync(a).mtime.getTime() -
                fs.statSync(b).mtime.getTime();
      });
    }

    if (files.length > 0){
      var gm = Gm()
      files.forEach(function(item){
        console.log(item)
        gm = gm.in(item)
      })
      //gm.delay(100)
      //  .resize(427,240)
      gm.limit('memory', '200MB')
        .delay(100)
        .resize(427,240)
        .write(dir+"/animated.gif", function(err){
          if (err) {
            if(cb){
              cb(err,null, null)
            } else {
              throw err
            }
            return;
          }
          console.log(dir+"/animated.gif created");
          if(cb){
            cb(null,dir+"/animated.gif",files)
          }
        });
    } else if(cb){
      cb('No File in folder: '+dir,null,null)
    }
  });
}

function _deleteFolderRecursive(path) {
    if( fs.existsSync(path) ) {
        fs.readdirSync(path).forEach(function(file) {
            var curPath = path + "/" + file;
            if(fs.statSync(curPath).isDirectory()) { // recurse
                deleteFolderRecursive(curPath);
            } else { // delete file
                fs.unlinkSync(curPath);
            }
        });
        fs.rmdirSync(path);
    }
};


function deleteFolderRecursive(path, face_motion_path) {
    if(!REMOVE_IMG_UPLOADED)
        return;

    // remove current unused images
    _deleteFolderRecursive(path)

    // remove all unused images and dirs
    if( fs.existsSync(face_motion_path) ) {
        fs.readdirSync(face_motion_path).forEach(function(dir) {
            var curPath = face_motion_path + "/" + dir;
            var dirstat = fs.statSync(curPath)
            if (dirstat && dirstat.ctime) {
              var tsdir = new Date(dirstat.ctime).getTime()
              if ((tsdir + 10*60*1000) < new Date().getTime() && fs.statSync(curPath).isDirectory()) {
                  _deleteFolderRecursive(face_motion_path + '/' + dir)
              }
            }
        });
    }
};

module.exports = {
  generateGif : generateGif,
  removeUnusedImageDir: deleteFolderRecursive
}
