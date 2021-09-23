# Machine Learning On The Edge, Turn your Camera into AI-powered with Jetson Nano

SharpAI is open source stack for machine learning engineering with private deployment and AutoML for edge computing.  DeepCamera is application of SharpAI designed for connect computer vision model to surveillance camera. Developers can run same code on Raspberry Pi/Android/PC/AWS to boost your AI production development.

## Todo 
- [x] FFMpeg with Nvidia Nano HW acceloration
- [x] Face Detector with Nvidia Nano HW acceloration [TensorRT MTCNN](https://github.com/jkjung-avt/tensorrt_demos)
- [ ] Face Embedding with Nvidia Nano HW acceloration
- [ ] Face ID Classifer with Nvidia Nano HW acceloration

# DeepCamera Architecture
![architecture](screenshots/DeepCamera_infrastructure.png)

## Demo On Youtube
[![Demo On Youtube](http://img.youtube.com/vi/LfcBN8UCy5k/0.jpg)](https://youtu.be/LfcBN8UCy5k)

# Get Started on Jetson Nano

## Install Docker-compose
```
sudo apt-get install -y libhdf5-dev python3 python3-pip
pip3 install -U pip
sudo pip3 install docker-compose==1.27.4
```

## Get source code
```
git clone https://github.com/SharpAI/DeepCamera
```

## Start DeepCamera
```
cd DeepCamera  
./run-on-nano.sh start
```
## Connect To Camera through RTSP URL

On Jetson Nano, Access to 8080 port.
http://localhost:8080   
Default username and password is:  
username: user@sharpaibox.com  
password: SharpAI2018

Tested Camera:
DaHua / Lorex / AMCREST,  URL Path: /cam/realmonitor?channel=1&subtype=0 Port: 554

## Label on Web GUI, train face recognition model on device
```
cat docker/workaipython/ro_serialno 
82f28703d001
```
`82f28703d001` is device ID.   

Access http://165.232.62.29:3000/

![how to config on web gui](screenshots/how_to_config_on_web_gui.png)


## [Detail information](https://github.com/SharpAI/DeepCamera/blob/master/docs/shinobi.md)   
## [Camera streaming URL format](https://shinobi.video)

## Use Mobile APP to label and train face recognition model on device
### Get device serial number
```
cat docker/workaipython/ro_serialno 
82f28703d001
```
`82f28703d001` is device ID.    
Generate QRCode of device ID

### Download and install [SharpAI Mobile APP](https://github.com/SharpAI/SharpAIMobileApp/releases/download/3.0.2/debug.apk)

### [Configure on Mobile APP](docs/configure_on_mobile.md)

# Develop your own Application GUI with DeepCamera API Server
If you don't like the GUI or you want to develop your own application.  
You can use following API:  

### Get device serial number
```
cat docker/workaipython/ro_serialno 
82f28703d001
```
`82f28703d001` is device ID
### Create User on API Server
REST API:
```
curl -X POST -H "Content-type: application/json" http://localhost:3000/api/v1/sign-up -d '{"username": "test11", "email": "xxxx@xxx.xx", "password": "xxxxxx"}'
```
Response:
```
{
  "success": true
}
```
### Get Token of created user
REST API:
```
curl -X POST -H "Content-type: application/json" http://localhost:3000/api/v1/login/ -d '{"username": "test11", "email": "xxxx@xxx.xx", "password": "123456"}'
```
Response:
```
{
  "status": "success",
  "data": {
    "authToken": "t6QsPaU3VdbfUQMkNIf6I3MDtox29WLrPJRAKkOCfpc",
    "userId": "tiK8RYG87sGJAErdB"
  }
}
```
### Create Group on API Server
Rest API:

Fill in `X-Auth-Token` and `X-User-Id` in previous response.
```
curl -X POST -H "X-Auth-Token: t6QsPaU3VdbfUQMkNIf6I3MDtox29WLrPJRAKkOCfpc" -H "X-User-Id: tiK8RYG87sGJAErdB" http://localhost:3000/api/v1/groups -d "name=group01"
```
Response:
```
{
  "groupId": "e309ff8c7a3a8ceb4011e86e"
}
```
### Add device to Group on API Server
REST API:
Replace `X-Auth-Token` and `X-User-Id`.
Replace group id in requesting URL: http://localhost:3000/api/v1/groups/`e309ff8c7a3a8ceb4011e86e`/devices
```
curl -X POST -H "X-Auth-Token: t6QsPaU3VdbfUQMkNIf6I3MDtox29WLrPJRAKkOCfpc" -H "X-User-Id: tiK8RYG87sGJAErdB" -H "Content-type: application/json" http://localhost:3000/api/v1/groups/e309ff8c7a3a8ceb4011e86e/devices -d '{"uuid": "82f28703d001", "deviceName": "testDevice", "name":"testdevice","type": "inout"}'
```
Response:
```
{
  "success": true
}
```

Then restart DeepCamera service.
### API Server document can be found here: [SharpAI/ApiServer](https://github.com/SharpAI/ApiServer#full-api-document)

### You can also develop/debug code on your PC [How to run DeepCamera On PC](docs/develop_on_pc.md)


# Deploy your own API_Server on X86/Cloud Server
Now, you got the idea of DeepCamera,  
the public testing server is open to the internet.  
You can deploy your own API server on your OWN device.  

```
git clone https://github.com/SharpAI/DeepCamera
cd DeepCamera
./start-cloud.sh start
```
You need ip address of private cloud server on next step (replace ip address to <Server_IP> on next step).  
If you don't want to setup your own server for now, a test server can be used for evaluation, the ip address of test server is 165.232.62.29


# If your have any question or feature request, please feel free to join slack for commercial support
## Slack
[Click to join sharpai slack channel](https://sharpai-invite-automation.herokuapp.com/)

## Feature List
- [ ] Porting to Jetson Nano 
- [x] High accurate Face Recognition
- [x] Face Detection
- [x] Inference on ARM Mali GPU
- [x] Support Android TF Lite(GPU/CPU/NPU)
- [x] Support open source embedded linux
- [x] Control from mobile application
- [x] Management System for devices
- [x] Push Notification to Mobile Device
- [x] Object Detection
- [x] Distributed System based on celery
- [x] Plugin to process video by Shinobi CCTV
- [x] Application on Android to decode video with hw acc
- [x] Motion Detection with Android GPU
- [x] Lable and train from Mobile to Edge Device
- [x] Native raspberry pi camera support
- [x] Labelling server and application is down, need BYOD document [API server repo](https://github.com/SharpAI/ApiServer)
- [x] Image upload to AWS or on premise AWS compatiable server(MINIO)

## [Contributions](Contributions.md)
