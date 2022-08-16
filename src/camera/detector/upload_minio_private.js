//const qiniu = require("qiniu");
const proc = require("process");
var fs = require('fs');
const Minio=require('minio')

function GetEnvironmentVarInt(varname, defaultvalue)
{
    var result = process.env[varname];
    if(result!=undefined)
        return parseInt(result,10);
    else
        return defaultvalue;
}

const AWS_END_POINT = process.env.AWS_END_POINT
const AWS_PORT = GetEnvironmentVarInt('AWS_PORT',80)
const AWS_USE_SSL = (process.env.AWS_USE_SSL === "true")
const AWS_ACCESS_KEY = process.env.AWS_ACCESS_KEY
const AWS_SECRET_KEY = process.env.AWS_SECRET_KEY
const AWS_BUCKET = process.env.AWS_BUCKET
const AWS_READABLE_PREFIX=process.env.AWS_READABLE_PREFIX

var mc = new Minio.Client({
    endPoint: AWS_END_POINT,
    port: AWS_PORT,
    useSSL: AWS_USE_SSL,
    accessKey: AWS_ACCESS_KEY,
    secretKey: AWS_SECRET_KEY
});

function ensureSharpAIBucketPublicReadalbe(cb){
  const BucketReadablePolicy={
  "Version":"2012-10-17",
  "Statement":[
    {
      "Sid":"PublicRead",
      "Effect":"Allow",
      "Principal": "*",
      "Action":["s3:GetObject","s3:GetObjectVersion"],
      "Resource":["arn:aws:s3:::"+AWS_BUCKET+"/*"]
    }
  ]
  }
  mc.setBucketPolicy(AWS_BUCKET, JSON.stringify(BucketReadablePolicy), function(err) {
    if (err) throw err
    console.log('Bucket policy set')
  })
}
function ensureSharpAIBucket(cb){
  mc.bucketExists(AWS_BUCKET, function(err, exists) {
    if (err || !exists) {
      console.log('storage bucket does not exist')
      console.log(err)
      mc.makeBucket(AWS_BUCKET, function(err) {
        if (err) {
          cb && cb(err)
          return console.log('Error creating bucket.', err)
        }
        console.log('Bucket created successfully')
        cb && cb(null)
        ensureSharpAIBucketPublicReadalbe()
      })
      return
    }
    if (exists) {
      cb && cb(null)
      ensureSharpAIBucketPublicReadalbe()
      return console.log('Bucket exists.')
    }
  })
}

function getAccessUrl(file_key){
  return AWS_READABLE_PREFIX+file_key;
}
function putFileAWS(file_key,localFile,cb){
  _putFileAWS(file_key,localFile,function(err, url){
    if(!err && url){
      cb && cb(null,url)
    } else {
      console.log('1st upload err, retry after 5s');
      setTimeout(function(){
      _putFileAWS(file_key,localFile,function(err, url){
          if(!err && url){
            cb && cb(null,url)
          } else {
            console.log('2nd upload err, retry after 15s');
            setTimeout(function(){
              _putFileAWS(file_key,localFile,function(err, url){
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
function _putFileAWS(file_key,localFile,cb){
  //if(obj.counter++ %2 === 0){ return cb('error',null)} test code for failed upload
  var read = fs.createReadStream(localFile);

  try{
    mc.putObject(AWS_BUCKET,file_key,read,function(err, etag){
      if(err){
        console.log('upload errr, need retry')
        if(cb){
          cb(err,null)
        }
        return
      }
      var access_url = getAccessUrl(file_key);
      console.log('upload succ to: '+access_url);
      if(cb){
        cb(null,access_url)
      }
    })
  } catch(e){
    console.log(e)
    console.log('exception when put object to aws')
    ensureSharpAIBucket(function(result){
      console.log('after ensureSharpAIBucket')
      console.log(result)
    })
  }
}

module.exports = {
  putFile : putFileAWS,
  getAccessUrl: getAccessUrl
}
