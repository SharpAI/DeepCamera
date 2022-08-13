//const qiniu = require("qiniu");
const proc = require("process");

var fs = require('fs');
var ALY = require('aliyun-sdk');

const OSS = require('ali-oss');
const client = new OSS({
  region: '',
  accessKeyId: '',
  accessKeySecret: '',
  bucket: ''
});

var bucket = '';
var accessKey = '';
var secretKey = '';

function getAccessUrl(file_key){
  return 'http://serverurl/'+file_key;
}
function putFileAliyun(file_key,localFile,cb){
  _putFileAliyun(file_key,localFile,function(err, url){
    if(!err && url){
      cb && cb(null,url)
    } else {
      console.log('1st upload err, retry after 5s');
      setTimeout(function(){
      _putFileAliyun(file_key,localFile,function(err, url){
          if(!err && url){
            cb && cb(null,url)
          } else {
            console.log('2nd upload err, retry after 15s');
            setTimeout(function(){
              _putFileAliyun(file_key,localFile,function(err, url){
                if(!err && url){
                  cb && cb(null,url)
                } else {

                  console.log('3rd upload err, gave up');
                  cb && cb('error',null)
                }
              })
            },15*1000)
          }
      })
    },5*1000);
   }
  })
}

//var obj = {counter:0}
function _putFileAliyun(file_key,localFile,cb){
  //if(obj.counter++ %2 === 0){ return cb('error',null)} test code for failed upload
  var read = fs.createReadStream(localFile);

  client.putStream(file_key,read).then((result) => {
    console.log(result);
    read.close()
    if(result && result.res && result.res.statusCode){
      var result_code = result.res.statusCode;
      if( result_code >= 200 && result_code <300){
        var file_name = file_key;
        if (result.name && result.name !==''){
          file_name = result.name;
        }
        var access_url = getAccessUrl(file_name);
        console.log('upload succ to: '+access_url);
        if(cb){
          cb(null,access_url)
        }
        return;
      }
    }
    console.log('upload errr, need retry');
    if(cb){
      cb('error',null)
    }
  });
}

module.exports = {
  putFile : putFileAliyun,
  getAccessUrl: getAccessUrl
}
/*putFile('animated.gif', "./images/animated.gif",function(error,url){
  if(error !== null){
    console.log('Error of upload')
  } else {
    console.log('Upload successed, file url is: '+url)
  }
})
putFile('hello_world.png', "./images/hello_world.png",function(error,url){
  if(error !== null){
    console.log('Error of upload')
  } else {
    console.log('Upload successed, file url is: '+url)
  }
})
*/
