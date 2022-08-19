# Face Recognition/Person Detection NVR

DeepCamera is a sample application from sharpai-hub.

## Get started on X86 Machine(Windows/Linux/Mac) / Jetson Nano (Jetpack 4.6) / More devices comming soon

### Installation
- Register account on [DeepCamera website](http://dp.sharpai.org:3000)
- Install sharpai-hub: `pip3 install sharpai-hub`
- Login on device: `sharpai-cli login`
- Register device: `sharpai-cli device register`
- Start DeepCamera: `sharpai-cli deepcamera start`

### Connect To Camera through NVR Gui

- NVR GUI(Shinobi) address: http://localhost:8080   
- Default username and password is:  
- username: user@sharpaibox.com  
- password: SharpAI2018

#### Tested Camera:
- DaHua / Lorex / AMCREST: URL Path: `/cam/realmonitor?channel=1&subtype=0` Port: `554`
- Ip Camera Lite on IOS: URL Path: `/live` Port: `8554`   

If you are using a camera but have no idea about the RTSP URL, please file an issue or use [iSpyConnect](https://www.ispyconnect.com/cameras) to get camera streaming URL format

## Features 
- [x] Install with SharpAI Hub CLI
- [x] FFMpeg with Nvidia Nano hardware decoder
- [x] Face Detector with Nvidia Nano GPU [TensorRT MTCNN](https://github.com/jkjung-avt/tensorrt_demos)
- [x] Face Embedding with Nvidia Nano GPU [Pytorch](https://github.com/nizhib/pytorch-insightface) [InsightFace](https://github.com/deepinsight/insightface) 
- [x] Person Detection with GPU
- [x] Integrate with telegram bot API
- [x] Porting to Jetson Nano 
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
## Todos
- [ ] Integration with Home Assistant

## Commercial Version
- Provide real time pipeline on edge device     
- E2E pipeline to support model customization  
- Cluster on the edge  
- Port to specific edge device/chipset
- Voice application (ASR/KWS) end to end pipeline  
- ReID model   
- Behavior analysis model    
- Transformer model  
- Contrastive learning  
- [Click to join sharpai slack channel for commercial support](https://sharpai-invite-automation.herokuapp.com/)

# DeepCamera Architecture
![architecture](screenshots/DeepCamera_infrastructure.png)

## Demo On Youtube
[![Demo On Youtube](http://img.youtube.com/vi/LfcBN8UCy5k/0.jpg)](https://youtu.be/LfcBN8UCy5k)

##  Install Docker-compose on Jetson Nano
```
sudo apt-get install -y libhdf5-dev python3 python3-pip
pip3 install -U pip
sudo pip3 install docker-compose==1.27.4
```
## Create Token for Telegram Bot
- Create Telegram Bot through @BotFather
- Set Telegram Token in [Configure File](https://github.com/SharpAI/DeepCamera/blob/nano/docker/production_1.env#L15)
- Send message to the new bot you created

![how to config on web gui](screenshots/how_to_config_on_web_gui.png)
## [Detail information](https://github.com/SharpAI/DeepCamera/blob/master/docs/shinobi.md)   
## [Camera streaming URL format](https://shinobi.video)

# If your have any question or feature request, please feel free to join slack for commercial support
## Slack
[Click to join sharpai slack channel](https://sharpai-invite-automation.herokuapp.com/)

## [Contributions](Contributions.md)
