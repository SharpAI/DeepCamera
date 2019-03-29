# [Quick Installation on Android](https://github.com/SharpAI/DeepCamera/releases/tag/v1.2.1)
1. Install DeepCamera AI monitor on Android. https://github.com/SharpAI/DeepCamera/releases/download/v1.2.1/DeepCamera_03282019.apk
2. Install mobile app to receive notification, name/labelling people(Beta test)  
Android: https://github.com/SharpAI/DeepCamera/releases/download/v1.2.1/sharpai-2.2.67-20190122181044.apk  
iOS: https://testflight.apple.com/join/8LXGgu3q

To speed up the evaluation of DeepCamera platform, SharpAI Dev Team developed an Application to use Android Camera instead of surveillance camera, remove hardware dependency will speed up the evaluation procedure for developers.

There would be some issues caused by Camera quality on the device, it always has better result if replace Android camera to surveillance camera but still, our Android AI camera is state-of-the-art production leveraging AutoML for Edge devices.



## Slack Channel
[Click to join sharpai slack channel](https://sharpai-invite-automation.herokuapp.com/)

# What's SharpAI DeepCamera
Deep Learning video processing surveillance on ARM GPU for face recognition and much more on the way. Turn digital camera into AI-powered camera. Production level platform for edge AI using ARM GPU/NPU, leveraging AutoML. The first world-class Edge AI full stack platform for developer/kids/home/SMB/enterprise/cloud, baking by community.

Full stack system for the deep learning edge computing devices, espeicailly set-up-box off the shell with image burning or Android apk installation.

## Data labeling on Mobile, no data scientist involed
## Automatically train/deploy model for edge device(Embedded/Android/X86 system)
## Power efficient, Easy scalable, Production ready, Mobile first

![image](screenshots/lifecycle_mac.png)

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

## Supported/tested Device
- [x] Raspberry Pi
- [x] X86 (Linux/Ubuntu, Mac OS X, Windows(not tested) through Docker)
- [x] Rockchip RK3399 (Linux, set-up-box H96 Max)
- [x] Rockchip RK3288 (Android, set-up-box)
- [x] Samsung 7420 (Android, Mobile)
- [x] Rockchip RK3399 (Android, RockPro64)
- [x] MediaTek MTK6797 (Android, Mobile/Tablet)
- [x] Huawei Kirin 960/970/980 （Android, Mobile/Tablet)
- [x] ARM 64bit devices

## Supported Camera
- [x] Dahua Camera
- [x] Hikvision Camera
- [x] Shinobi CCTV Supported Devices
- [x] Screen Captured from Android Camera preview application

## Demo
![demo](https://github.com/SharpAI/DeepCamera/blob/master/screenshots/demo.gif)

## How to develop on SharpAI DeepCamera

You can develop on SharpAI DeepCamera almost on every devices.

### [How to Run DeepCamera on 64-bit Android From Source Code](docs/Run_Source_Android_aarch64.md)
### [How to Run DeepCamera on 32-bit Android](docs/RunOnRK3288.md)
### [Run on Raspberry Pi](docs/RunOnRaspberryPi.md)
### Run on Embedded Linux with docker (Rockchip RK3399)
```
git clone https://github.com/SharpAI/DeepCamera
cd DeepCamera/docker  
sudo ./run-deepeye-prebuilt.sh start
```
### Run on X86 Laptop Docker
```
git clone https://github.com/SharpAI/DeepCamera -b pc_version
cd DeepCamera/docker
sudo ./run-deepeye-x86.sh start #make sure Serial No is in docker/workaipython/ro_serialno
```   

## It is even possible to connect Surveilance Camera 

### Through Shinobi (if you install DeepCamera through Docker)
Then you need to follow [Shinobi's document](https://shinobi.video) to add camera. or [click to see our tutorial](https://github.com/SharpAI/DeepCamera/blob/master/docs/shinobi.md)

Shinobi login page(device_ip:8080):   
username: user@sharpaibox.com  
password: SharpAI2018 

You can also [turn Mac Camera into RTSP camera(not tested)](https://www.tribler.org/MacWebcam/)

### Through Dahua SDK (if you install DeepCamera on Android)
Code is [here](https://github.com/SharpAI/RTSP_Decoder_IJKPlayer/blob/od_gl_based/android/ijkplayer/ijkplayer-example/src/main/java/tv/danmaku/ijk/media/example/activities/CameraScanActivity.java#L147)


## Survey: Do you want to have Dev Kit for easily startup
We are considering to provide full set of development kit to easy the setup effort you may face to. 
[Please thumb up if you want one](https://github.com/SharpAI/DeepCamera/issues/8)

### How it works from end user's point of view, green parts are done if using Dev Kit
![From end user's view](screenshots/on_app_end_user.png)

## [How to configure on Mobile APP, Chinese Version](https://github.com/SharpAI/mobile_app_server/blob/android_porting/README.md)

## Application in English(Beta Test)
Android: https://www.pgyer.com/app/install/0e87e08c72a232e8f39a6a7c76222038  
iOS: https://testflight.apple.com/join/8LXGgu3q

## [How to deploy server on your server](https://github.com/SharpAI/mobile_app_server/issues/1)
# Call For Help
- [x] Translation, we did deploy our production in China, much of our resource is in Chinese, need your help to translate, especially the Mobile APP built with Meteor https://github.com/SharpAI/mobile_app_server  (English_Version)
- [x] Remove unused code/project in https://github.com/SharpAI/mobile_app_server
- [x] PR, more than welcome, anything :)
- [ ] Meetup hosts, in Silicon Valley

![screen shot 2019-03-07 at 4 03 59 pm](https://user-images.githubusercontent.com/3085564/53941268-a0781b80-40f2-11e9-8cc6-6295c3a39c96.png)

![deepcamera_arm32 on android](screenshots/deepcamera_arm32.png)
![deepcamera_arm64 on android](screenshots/deepcamera_arm64.png)
![deepcamera_on docker linux](screenshots/deepcamera_docker_linux.png)

![screen shot 2019-03-07 at 11 27 22 am](https://user-images.githubusercontent.com/3085564/53930362-fdaca680-40cb-11e9-8303-d538315d9021.png)

![screen shot 2019-03-07 at 11 30 54 am](https://user-images.githubusercontent.com/3085564/53930505-7c094880-40cc-11e9-939a-1368cc557a0c.png)
 
## APIs doc for app server
[Click to see APIs document](https://github.com/SharpAI/mobile_app_server/tree/android_porting/rest_api_sdk)

## App User Guide
[Click for user guide](https://github.com/SharpAI/mobile_app_server/blob/android_porting/README.md)

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
