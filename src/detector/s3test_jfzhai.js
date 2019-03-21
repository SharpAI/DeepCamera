const S3MinioUpload = require('./s3uploader');
const S3Conf = require('./s3Conf.json');


console.log('---------test-----------');

var filePath = '/Users/zhaijunfeng/Desktop/640.jpeg';
var fileName = '640.jpeg';


S3MinioUpload.init(S3Conf.Config).uploadObject('stream', filePath);
S3MinioUpload.init(S3Conf.Config).getAccessUrl('stream');