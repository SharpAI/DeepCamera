const proc = require("process");
var fs = require('fs');

function GetEnvironmentVarInt(varname, defaultvalue)
{
    var result = process.env[varname];
    if(result!=undefined)
        return parseInt(result,10);
    else
        return defaultvalue;
}



function getAccessUrl(file_key){
  return AWS_READABLE_PREFIX+file_key;
}
function putFileAWS(file_key,localFile,cb){
  _putFileAWS(file_key,localFile,function(err, url){
    if(!err && url){
      cb && cb(null,url)
    } else {
      console.log('1st upload failed, retry after 5s');
      setTimeout(function(){
      _putFileAWS(file_key,localFile,function(err, url){
          if(!err && url){
            cb && cb(null,url)
          } else {
            console.log('2nd upload failed, retry after 15s');
            setTimeout(function(){
              _putFileAWS(file_key,localFile,function(err, url){
                if(!err && url){
                  cb && cb(null,url)
                } else {

                  console.log('3rd upload failed, no more retry');
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
function _putFileAWS(file_key,localFile,cb){

}

module.exports = {
  putFile : putFileAWS,
  getAccessUrl: getAccessUrl
}
