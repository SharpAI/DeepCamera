# What's SharpAI DeepCamera
Deep Learning video processing surveillance on ARM GPU for face recognition and much more on the way. Turn digital camera into AI-powered camera. Production level platform for edge AI using ARM GPU/NPU, leveraging AutoML. The first world-class Edge AI full stack platform for developer/kids/home/SMB/enterprise/cloud, baking by community.

Full stack system for the deep learning edge computing devices, espeicailly set-up-box off the shell with image burning or Android apk installation.

## Data labeling on Mobile, no data scientist involed
## Automatically train/deploy model for edge device(Embedded/Android/X86 system)
## Power efficient, Easy scalable, Production ready, Mobile first

![image](screenshots/lifecycle_mac.png)

# Feature List
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

# Supported Device
- [x] Raspberry Pi
- [x] X86 (Linux/Ubuntu, Mac OS X, Windows(not tested) through Docker)
- [x] Rockchip RK3399 (Linux, set-up-box H96 Max)
- [x] Rockchip RK3288 (Android, set-up-box)
- [x] Samsung 7420 (Android, Mobile)
- [x] Rockchip RK3399 (Android RockPro64 doc release soon)
- [x] Linux/Android Has OpenCL

# Supported Camera
- [x] Dahua Camera
- [x] Hikvision Camera
- [x] Shinobi CCTV Supported Devices
- [x] Screen Captured from Android Camera preview application

# Slack Channel
[Click to join sharpai slack channel](https://sharpai-invite-automation.herokuapp.com/)

# Demo
![demo](https://github.com/SharpAI/DeepCamera/blob/master/screenshots/demo.gif)

# How to Run DeepCamera From Source Code
![From end user's view](screenshots/on_app_end_user.png)

## 1. Generate/Get Serial No
### Android
After install Launcher(Modified Termux), the serial_no will be placed:
`/data/data/com.termux/files/home/.ro_serialno`
### Linux/MacOS
Get your Mac Address(1e:20:34:10:24:21)
```
cd DeepCamera
echo 1e2034102421 > docker/workaipython/ro_serialno
```
## 2. Then generate text type QR code with serial_no you just got
[QR code Generator En](https://www.qr-code-generator.com)  
[QR code Generator Chn](https://cli.im/)

## 3. How to Run DeepCamera on Edge Device

### 3.1 [Run on Android(5.1+ aarch64)](docs/Run_On_Android_aarch64.md)
### 3.2 Run on Rockchip RK3399 with linux/docker
#### 3.2.1 Use prebuilt docker images
```
git clone https://github.com/SharpAI/DeepCamera
cd DeepCamera/docker  
sudo ./run-deepeye-prebuilt.sh start
```
### 3.3 [Run on Rockchip RK3288 with Android 5.1](docs/RunOnRK3288.md)
### 3.4 Run on X86 Laptop Docker
#### 3.4.1 Use prebuilt docker images
```
git clone https://github.com/SharpAI/DeepCamera -b pc_version
cd DeepCamera/docker
sudo ./run-deepeye-x86.sh start #make sure Serial No is in docker/workaipython/ro_serialno
```   
#### 3.4.2 Build docker images on your local machine
```
git clone https://github.com/SharpAI/ImageBuilder-DeepLearning -b android_porting
cd ImageBuilder-DeepLearning/Docker-DeepEye/workai/
./build_x86_dockers.sh
```
Then run DeepCamera, will use local docker images

```
git clone https://github.com/SharpAI/DeepCamera
cd DeepCamera/docker
docker-compose -f docker-compose-x86.yml up
```

### 3.5 [Run on Raspberry Pi](docs/RunOnRaspberryPi.md)

## 4. Link to Your Camera 

### 4.1 Linux/Docker System
Then you need to follow [Shinobi's document](https://shinobi.video) to add camera. or [click to see our tutorial](https://github.com/SharpAI/DeepCamera/blob/master/docs/shinobi.md)

Shinobi login page(device_ip:8080):   
username: user@sharpaibox.com  
password: SharpAI2018 

You can also [turn Mac Camera into RTSP camera(not tested)](https://www.tribler.org/MacWebcam/)

### 4.2 Android(Dahua SDK Configure)
Code is [here](https://github.com/SharpAI/RTSP_Decoder_IJKPlayer/blob/od_gl_based/android/ijkplayer/ijkplayer-example/src/main/java/tv/danmaku/ijk/media/example/activities/CameraScanActivity.java#L147)

### 4.3 Android screen capture
Code is [here](https://github.com/SharpAI/ScreenCapture)

### 4.4 Android(RTSP url config)
Comming soon

# Survey: Do you want to have Dev Kit for easily startup
We are considering to provide full set of development kit to easy the setup effort you may face to. 
[Please thumb up if you want one](https://github.com/SharpAI/DeepCamera/issues/8)
### How it works from end user's point of view, green parts are done if using Dev Kit
![From end user's view](screenshots/on_app_end_user.png)

## [How to configure on Mobile APP](https://github.com/SharpAI/mobile_app_server/blob/android_porting/README.md)
## [How to deploy server on your server](https://github.com/SharpAI/mobile_app_server/issues/1)
# Call For Help
- [ ] Documents, A LOT OF DOCUMENTS, we already deploy our deep camera in industry leading company but we don't have extra resource to build up community friendly documents.
- [ ] Tutorial on youtube, we can build up some of them, only if with your help, we can success together.
- [ ] Translation, we did deploy our production in China, much of our resource is in Chinese, need your help to translate, especially the Mobile APP built with Meteor https://github.com/SharpAI/mobile_app_server  (need i18n selection based on system language)
- [ ] Remove unused code/project in https://github.com/SharpAI/mobile_app_server
- [ ] PR, more than welcome, anything :)
- [ ] Meetup hosts, in Silicon Valley

![screen shot 2019-03-07 at 4 03 59 pm](https://user-images.githubusercontent.com/3085564/53941268-a0781b80-40f2-11e9-8cc6-6295c3a39c96.png)

![deepcamera_arm32 on android](screenshots/deepcamera_arm32.png)
![deepcamera_arm64 on android](screenshots/deepcamera_arm64.png)
![deepcamera_on docker linux](screenshots/deepcamera_docker_linux.png)

![screen shot 2019-03-07 at 11 27 22 am](https://user-images.githubusercontent.com/3085564/53930362-fdaca680-40cb-11e9-8303-d538315d9021.png)

![screen shot 2019-03-07 at 11 30 54 am](https://user-images.githubusercontent.com/3085564/53930505-7c094880-40cc-11e9-939a-1368cc557a0c.png)
 
# APIs doc for app server
[Click to see APIs document](https://github.com/SharpAI/mobile_app_server/tree/android_porting/rest_api_sdk)

# App User Guide
[Click for user guide](https://github.com/SharpAI/mobile_app_server/blob/android_porting/README.md)
