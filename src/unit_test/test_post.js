var request = require('request');
/*
var filename = '/storage/emulated/0/Download/frame_30112018_040438_229.jpg';
request.get(
    'http://192.168.0.38:3000/api/post?url='+filename,
    function (error, response, body) {
        if (!error && response.statusCode == 200) {
            console.log(body)
        }
    }
);
*/
request.get(
    'http://192.168.0.38:3000/api/test1080',
    function (error, response, body) {
        if (!error && response.statusCode == 200) {
            console.log(body)
        }
    }
);
