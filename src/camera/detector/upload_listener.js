const config=require('config')
const Minio=require('minio')
const path = require("path")

var mcConfig = config.get('config');
// Allocate a new minio-js client.
if (mcConfig.endPoint === '<endpoint>') {
    console.log('Please configure your endpoint in \"config/webhook.json\".');
    process.exit(1);
}
var mc = new Minio.Client(mcConfig)
var sharpai_onframe=null

function listenToSharpAIBucket(){
  let poller = mc.listenBucketNotification('sharpai', '', '.jpg', ['s3:ObjectCreated:*'])
  poller.on('notification', record => {
      console.log('New object: %s/%s (size: %d)', record.s3.bucket.name,
                  record.s3.object.key, record.s3.object.size)
      var saving_filename = new Date().getTime()+'_'+record.s3.object.key
      var absolutePath = path.resolve(saving_filename)

      mc.fGetObject(record.s3.bucket.name,record.s3.object.key,saving_filename,function(err){
        console.log('safed file to ',absolutePath)

        if(sharpai_onframe){
          console.log('save key then process it')

           var undefined_obj
           var start = new Date()
           sharpai_onframe("uploaded", true, absolutePath, undefined_obj, start)
        }

        mc.removeObject(record.s3.bucket.name, record.s3.object.key, function(err) {
          if (err) {
            return console.log('Unable to remove object', err)
          }
          console.log('Removed the object',record.s3.object.key,' on minio')
        })
      })
  })
}
function ensureSharpAIBucket(cb){
  mc.bucketExists('sharpai', function(err, exists) {
    if (err || !exists) {
      console.log('sharpai bucket does not exist')
      console.log(err)
      mc.makeBucket('sharpai', function(err) {
        if (err) {
          cb && cb(err)
          return console.log('Error creating bucket.', err)
        }
        console.log('Bucket created successfully')
        cb && cb(null)
      })
      return
    }
    if (exists) {
      cb && cb(null)
      return console.log('Bucket exists.')
    }
  })
}
module.exports = {
  init : function(onframe){
    sharpai_onframe=onframe
    ensureSharpAIBucket(function(){
      listenToSharpAIBucket()
    })
    console.log('upload listerer is ready')
  }
}
