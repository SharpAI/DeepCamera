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
let poller = mc.listenBucketNotification('sharpai', '', '.jpg', ['s3:ObjectCreated:*'])
var sharpai_onframe=null

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
    // Now that we've received our notification, we can cancel the listener.
    // We could leave it open if we wanted to continue to receive notifications.
    //poller.stop()
})

module.exports = {
  init : function(onframe){
    sharpai_onframe=onframe
    console.log('upload listerer is ready')
  }
}
