var request = require('request')

var od_host_ip='172.19.0.6'
var object_detection_task_url = 'http://'+od_host_ip+':5555/api/task/apply/od.detection'

var test_urls = ['/opt/nvr/detector/images/000000000285.jpg','/opt/nvr/detector/images/000000005992.jpg']

test_urls.forEach(function(item){
	var ts = new Date().getTime()
	trackerid = ts
	cameraId = 'dahua_DH'
	var json_request_content = {'args': [item, trackerid, ts, cameraId]};
	request({
	    url: object_detection_task_url,
	    method: "POST",
	    json: true,
	    body: json_request_content
	}, function (error, response, body){
	    //console.log(response)
	    if(error) {
	        console.log(error)
	    } else {
	        console.log(body)
      }
	})
})
