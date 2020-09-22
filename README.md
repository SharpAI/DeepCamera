# What's SharpAI DeepCamera
SharpAI is open source stack for machine learning engineering. DeepCamera is application of SharpAI designed for computer vision. Developers can run same code on Raspberry Pi/Android/PC/AWS.
![image](screenshots/lifecycle_mac.png)

## DeepCamera Architecture
![architecture](screenshots/DeepCamera_infrastructure.png)

## Feature List
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
- [ ] Image upload is not working(was using Aliyun), need change to upload to server itself

## Commercial Support
### Slack
[Click to join sharpai slack channel](https://sharpai-invite-automation.herokuapp.com/)

## Demo
![demo](https://github.com/SharpAI/DeepCamera/raw/master/screenshots/demo.gif)

# Get Started

## On X86 Linux
1. Install Docker
```
sudo curl -sSL https://get.docker.com | sh
```
2. Get source code
```
git clone https://github.com/SharpAI/DeepCamera
```
3. Start container
```
cd DeepCamera/
./run-on-linux.sh start
```
## On OSX
1. Install Docker
[Install Docker Desktop on Mac(Offical)](https://docs.docker.com/docker-for-mac/install/)
2. Get source code
```
git clone https://github.com/SharpAI/DeepCamera
```
3. Start container
```
cd DeepCamera/
./run-on-mac.sh start
```

## [On Raspberry Pi 3B+/4B](docs/RUN_ON_PI_V2.md)

## Connect Streaming
### Through Open Source NVR

Shinobi login page(device_ip:8080):   
username: user@sharpaibox.com  
password: SharpAI2018 

Change IP configuration and camera url on the page. [Detail information](https://github.com/SharpAI/DeepCamera/blob/master/docs/shinobi.md)   
If you are using other camera support streaming, please check [The Shinobi NVR's document](https://shinobi.video)  [Supported Devices](docs/Supported_Devices.md)

## Connect DeepCamera to API Server(Doc WIP)

### Get device serial number
### Create User on API Server
### Create Group on API Server
### Add device to Group on API Server

## Contributions
This project contains source code or library dependencies from the follow projects:
* Tensorflow available at: https://github.com/tensorflow/tensorflow Apache License 2.0
* MXNet available at: https://github.com/apache/incubator-mxnet Apache License 2.0
* TVM available at: https://github.com/dmlc/tvm Apache License 2.0
* Shinobi project available at: https://gitlab.com/Shinobi-Systems/Shinobi/ Copyright (c) 2018 Shinobi Systems
* Termux project available at: https://github.com/termux/termux-app GPLv3/Apache License 2.0
* Insightface project available at: https://github.com/deepinsight/insightface MIT License
* Easyrs project available at: https://github.com/silvaren/easyrs MIT License
* Nodejs: https://nodejs.org Copyright Node.js contributors. All rights reserved.
* Python: https://www.python.org Python 2.7 license
* Gcc for termux with fortran scipy etc: https://github.com/its-pointless/gcc_termux
* RembrandtAndroid project available at https://github.com/imgly/RembrandtAndroid
* Great English-writing introduction on [analyticsvidhya](https://www.analyticsvidhya.com/blog/2019/04/top-5-machine-learning-github-reddit/)
