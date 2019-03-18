const AWS = require('aws-sdk');
const fs = require('fs');
const path = require('path');


//configuring the AWS environment
AWS.config.update({
    endpoint: 'http://10.20.10.86:9000',
    accessKeyId: "A5DJSFROAY6RITEQ28D6",
    secretAccessKey: "uc/+vk+y37ptneWO11Lz+x5JV01b1wavlGBjmFik",
    s3ForcePathStyle: true, // needed with minio?
    signatureVersion: 'v4'
  });

var s3 = new AWS.S3();
var filePath = "./test.js";

//configuring parameters
var params = {
  Bucket: 'sharpai',
  Body : fs.createReadStream(filePath),
  Key : "folder/"+Date.now()+"_"+path.basename(filePath)
};

s3.upload(params, function (err, data) {
  //handle error
  if (err) {
    console.log("Error", err);
  }

  //success
  if (data) {
    console.log("Uploaded in:", data.Location);
  }
});
