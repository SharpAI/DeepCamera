## How to build your own server from open source code
```
mkdir local_installation
cd local_installation
git clone https://github.com/SharpAI/SharpAIMobileApp -b webhome
git clone https://github.com/SharpAI/ApiServer
curl https://install.meteor.com/ | sh
cd SharpAIMobileApp
meteor run
```

## Configure DeepCamera to post information to your own device/service

### Edit ~/.sharpai/deepcamera/.env

```
# AWS configuration
AWS_END_POINT=dp.sharpai.org
AWS_PORT=9000
AWS_USE_SSL=false
AWS_ACCESS_KEY=QUA2IU17RHOKE6NUZ7T2
AWS_SECRET_KEY=MQniMc5K3lsRbv9OPaUbJN9ft2eTQJ1rh4Yx6C17
AWS_BUCKET=faces
AWS_READABLE_PREFIX=http://dp.sharpai.org:9000/faces/

# Server configuration
MQTT_BROKER_ADDRESS=dp.sharpai.org
MQTT_BROKER_PORT=1883
MQTT_BROKER_TRANSPORT=tcp
API_SERVER_ADDRESS=dp.sharpai.org
API_SERVER_PORT=3000
```

## Replace upload.js to upload image to your own aws service.

```
docker exec -ti detector_plugin /bin/bash
cd /opt/nvr/detector
cp upload_minio_private.js upload.js
exit
docker restart detector_plugin 
docker restart embedding 
```
