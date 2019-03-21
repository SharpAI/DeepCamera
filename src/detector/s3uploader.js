var S3MinioUpload = {
    s3Config: null,
    minioClient: null,
    policy: null,

    /**
     * init method,return S3MinioUpload object
     * @param {obj} s3Config is must 
     * @param {*} policy Not a must 
     */
    init: function(s3Config, policy) {
        var me = this;

        if (s3Config) {
            me.s3Config = s3Config;
        } else {
            var msg = 's3Config is must';
            console.error(msg);
            throw msg;
        }
        var Minio = require('minio');
        me.minioClient = new Minio.Client({
            endPoint: me.s3Config.endPoint,
            port: me.s3Config.port,
            useSSL: me.s3Config.useSSL,
            accessKey: me.s3Config.accessKey,
            secretKey: me.s3Config.secretKey
        });

        if (policy) {
            me.policy = policy;
        } else {
            me.policy = {
                "Version": "2012-10-17",
                "Statement": [{
                        "Action": [
                            "s3:GetBucketLocation",
                            "s3:ListBucket"
                        ],
                        "Effect": "Allow",
                        "Principal": {
                            "AWS": [
                                "*"
                            ]
                        },
                        "Resource": [
                            "arn:aws:s3:::" + me.s3Config.bucketName
                        ],
                        "Sid": ""
                    },
                    {
                        "Action": [
                            "s3:GetObject"
                        ],
                        "Effect": "Allow",
                        "Principal": {
                            "AWS": [
                                "*"
                            ]
                        },
                        "Resource": [
                            "arn:aws:s3:::" + me.s3Config.bucketName + "/*"
                        ],
                        "Sid": ""
                    }
                ]
            };
        }

        console.log('s3Config:' + JSON.stringify(me.s3Config));
        console.log('s3 policy:' + JSON.stringify(me.policy));

        return me;
    },



    /**
     * 
     * @param {str} key file name...
     * @param {str} filePath local path
     */
    uploadFile: function(key, filePath, callback) {
        var me = this;

        me.minioClient.bucketExists(me.s3Config.bucketName, function(err, exists) {
            if (err) {
                return console.log('bucketExists err:' + err);
            }

            if (exists) {
                console.log('Bucket exists.' + me.s3Config.bucketName + ' ,will upload...');
                var metaData = {
                    'Content-Type': 'application/octet-stream',
                    'X-Amz-Meta-Testing': 1234,
                    'example': 5678
                };
                // Using fPutObject API upload your file to the bucket .
                me.minioClient.fPutObject(me.s3Config.bucketName, key, filePath, metaData, function(err, etag) {
                    if (err) {
                        return console.log(err);
                    } else {
                        console.log('File uploaded successfully.' + filePath);

                        callback && callback(null, me.getAccessUrl(key));
                    }
                });
            } else {
                console.log('Bucket not exists.' + me.s3Config.bucketName + ' please create bucket');

            }
        });
    },


    uploadObject: function(key, filePath, callback) {

        var me = this;

        me.minioClient.bucketExists(me.s3Config.bucketName, function(err, exists) {
            if (err) {
                return console.log('bucketExists err:' + err);
            }

            if (exists) {
                console.log('Bucket exists.' + me.s3Config.bucketName + ' ,will upload...');

                var Fs = require('fs')
                var fileStream = Fs.createReadStream(filePath);
                var fileStat = Fs.stat(filePath, function(err, stats) {
                    if (err) {
                        return console.log(err);
                    }
                    me.minioClient.putObject(me.s3Config.bucketName, key, fileStream, stats.size, function(err, etag) {
                        if (err) {
                            return console.log(err, etag); // err should be null
                        } else {
                            console.log('File stream uploaded successfully.' + filePath);

                            callback && callback(null, me.getAccessUrl(key));
                        }

                    });
                });
            } else {
                console.log('Bucket not exists.' + me.s3Config.bucketName + ' please create bucket');

            }
        });

    },

    /**
     * if bucket not exits ,create it
     */
    makeBucket: function() {
        var me = this;

        me.minioClient.bucketExists(me.s3Config.bucketName, function(err, exists) {
            if (err) {
                return console.log('bucketExists err:' + err);
            }

            if (exists) {
                console.log('Bucket exists.' + me.s3Config.bucketName);
            } else {
                console.log('--minioClient.makeBucket--');
                // Make a bucket called .
                me.minioClient.makeBucket(me.s3Config.bucketName, me.s3Config.region, function(err) {
                    if (err) {
                        return console.log('makeBucket:' + err);
                    } else {
                        console.log('Bucket created successfully in "us-east-1".' + me.s3Config.bucketName);
                    }
                });
            }
        });
    },


    /**
     *  With token information access path, the validity of the default one day
     * 
     * @param {*} key 
     * @param {*} callback 
     */
    presignedUrl: function(key, callback) {
        var me = this;

        me.minioClient.presignedUrl('GET', me.s3Config.bucketName, key, 1 * 24 * 60 * 60, function(err, presignedUrl) {
            if (err) return console.log(err);
            console.log('presignedUrl' + presignedUrl);

            callback && callback(presignedUrl);
        });
    },

    /**
     * With token information access path, the validity of the default one day
     * @param {*} key 
     * @param {*} callback 
     */
    presignedGetObject: function(key, callback) {
        var me = this;
        // expires in a day.
        me.minioClient.presignedGetObject(me.s3Config.bucketName, key, 1 * 24 * 60 * 60, function(err, presignedUrl) {
            if (err) return console.log(err);
            console.log('presignedGetObject' + presignedUrl);

            callback && callback(presignedUrl);
        });
    },

    getBucketPolicy: function() {
        var me = this;

        me.minioClient.getBucketPolicy(me.s3Config.bucketName, function(err, policy) {
            // if (err) throw err
            if (err) console.log(err);
            console.log(`Bucket policy : ` + JSON.stringify(policy));
        })
    },

    /**
     * 
     * @param {json obj} policy 
     */
    setBucketPolicy: function(policy) {
        var me = this;

        me.minioClient.setBucketPolicy(me.s3Config.bucketName, JSON.stringify(policy), function(err) {
            // if (err) throw err
            //code: 'UnknownError',依然set成功，暂时不知道原因
            if (err) console.log(err);
            console.log('Bucket policy set');
        });
    },
    /**
     * must set bucket policy
     * @param {*} key 
     */
    getAccessUrl: function(key) {
        var me = this;

        var agreement = me.s3Config.useSSL ? "https://" : "http://";
        var url = agreement + me.s3Config.endPoint + ':' + me.s3Config.port + '/' + me.s3Config.bucketName + '/' + key;
        console.log(url);
        return url;
    }

};

module.exports = S3MinioUpload;