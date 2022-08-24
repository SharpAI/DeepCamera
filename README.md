# AI Empowered NVR 

SharpAI help you deploy AI empowered NVR on your edge device in minutes.

# Install SharpAI on Jetson Nano/Xavier AGX/Windows/Linux/MacOS
- Register account on [SharpAI website](http://dp.sharpai.org:3000)
- Install sharpai-hub: `pip3 install sharpai-hub`
- Login on device: `sharpai-cli login`
- Register device: `sharpai-cli device register`

# Start Applications

## DeepCamera Face Recognition NVR
DeepCamera is a face recongnition NVR

```
sharpai-cli deepcamera start
```

## Yolo Parking
Maintaining empty parking spot count using YOLO real-time vehicle detection. [Original Link](https://github.com/ankit1khare/Smart-Park-with-YOLO-V3)

```
sharpai-cli yoloparking start
```
### Then access Linux GUI http://localhost:8000 w/ pre-configured noVNC

# Connect RTSP camera source to NVR
You need to get the RTSP url of your camera and add it to NVR. Then NVR engine will pull video stream through RTSP protocol from your camera, after extracting frame from video stream, the extracted frame will be sent to detector for AI tasks.

- NVR GUI address: http://localhost:8080   

# Tested Devices

## Edge AI Devices / Workstation
- [Jetson Nano (ReComputer j1010)](https://www.seeedstudio.com/Jetson-10-1-H0-p-5335.html)
- Jetson Xavier AGX
- MacOS 12.4
- Windows 11
- Ubuntu 20.04

## Tested Camera:
- DaHua / Lorex / AMCREST: URL Path: `/cam/realmonitor?channel=1&subtype=0` Port: `554`
- Ip Camera Lite on IOS: URL Path: `/live` Port: `8554`   

# Support
If you are using a camera but have no idea about the RTSP URL, please join SharpAI community for help or use [iSpyConnect](https://www.ispyconnect.com/cameras) to get camera streaming URL format. SharpAI provides commercial support to companies which want to deploy AI Camera application to real world.

## [Click to join sharpai slack channel](https://sharpai-invite-automation.herokuapp.com/)

# DeepCamera Architecture
![architecture](screenshots/DeepCamera_infrastructure.png)

# Features 
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
# Todos
- [ ] Integration with Home Assistant

# Commercial Version
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

# FAQ
##  How to install Docker-compose on Jetson Nano
```
sudo apt-get install -y libhdf5-dev python3 python3-pip
pip3 install -U pip
sudo pip3 install docker-compose==1.27.4
```
## [How to use web gui](screenshots/how_to_config_on_web_gui.png)
## [How to config RTSP on GUI](https://github.com/SharpAI/DeepCamera/blob/master/docs/shinobi.md)   
## [Camera streaming URL format](https://shinobi.video)
## How to create token for Telegram Bot(DOC W.I.P)
- Create Telegram Bot through @BotFather
- Set Telegram Token in [Configure File](https://github.com/SharpAI/DeepCamera/blob/nano/docker/production_1.env#L15)
- Send message to the new bot you created

## [Contributions](Contributions.md)
