var request = require('request');

request({
    method: 'POST',
    url: 'http://127.0.0.1:5050/classify_full',
    // body: '{"foo": "bar"}'
    json: {"foo": "bar"}
}, (error, response, body) => {
    console.log(error);
    // console.log(response);
    console.log(body);
});
