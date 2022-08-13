var request = require('request')
//https://arlos3-prod-z2.s3.amazonaws.com/f56ed590_ef56_43bb_ba26_04f4810ae54d/MG4YV9-336-32468109/59U17B78B3D97/recordings/1524182930703.mp4?AWSAccessKeyId=AKIAICS2UAC4WFSD6C2A&Expires=1524269367&Signature=ho9Xs86Gy2kY9oCywIqHoTsucZ8%3D
var test_urls = ['https://github.com/solderzzc/test_image/releases/download/1/1524163542928.mp4'
]

console.log('in test_post')


test_urls.forEach(function(item){
  request({
      url:'http://localhost:8088/api/insert',
      method: 'POST',
      json: true,
      body:{ download_url: item}
    },
    function (error, response, body) {
        if (!error && response.statusCode == 200) {
            console.log(body)
        } else {
          console.log(error)
        }
    }
  );
})
