# AI Empowered NVR 

SharpAI help you deploy AI empowered NVR on your edge device in minutes.

# Install SharpAI on Jetson Nano/Xavier AGX/Windows/Linux/MacOS
- Register account on [SharpAI website](http://dp.sharpai.org:3000)
- Install sharpai-hub: `pip3 install sharpai-hub`
- Login on device: `sharpai-cli login`
- Register device: `sharpai-cli device register`

# Start Applications

## DeepCamera Face Recognition NVR
- DeepCamera is a face recongnition NVR leverages [MTCNN](https://arxiv.org/abs/1604.02878) for face detection and [InsightFace's ArcFace](https://arxiv.org/abs/1801.07698) for face recognition, it leverages SVM from SKLearn as classifier and a private implemetation from Frank Zuo to fine-tune accuracy. To handle unbalanced dataset distribution which is most likely seen when you start to labelling unknown faces, we deployed upsampling policy to your own labelled face dataset. All the inference code as well as AutoML training code are running on your own device. 
- The DeepCamera commerical version which had been deployed to a large-scale AI smart city construction project has strong backend design to support large scale edge device cluster with redis. The commerical version provides private cloud deployment for security requirement.
- Learned from the open source community, it was a painful procedure to deploy a private cloud solution on your own device, we provide free cloud host for evaluation and non-commericial use with limited storage quota, so you can easily use following command line to setup DeepCamera on your own device in 5-minutes:

```
sharpai-cli deepcamera start
```

## Yolo Parking
Maintaining empty parking spot count using YOLO real-time vehicle detection, this is an original version for evaluation, we are planning to bring yolov7 to this interesting application. [Github Link](https://github.com/SharpAI/YoloParking)

```
sharpai-cli yoloparking start
```
#### Linux Desktop GUI is accessible through http://localhost:8000, thanks to open source web vnc client [noVNC](https://novnc.com/info.html), we don't have to install any software on the computer to remote access a edge device.

## Fall Detection

Using Tiny-YOLO oneclass to detect each person in the frame and use AlphaPose to get skeleton-pose and then use ST-GCN model to predict action from every 30 frames of each person tracks. [Github Link](https://github.com/SharpAI/FallDetection)
```
sharpai-cli falldetection start
```
#### Linux Desktop GUI is accessible through http://localhost:8000, thanks to open source web vnc client [noVNC](https://novnc.com/info.html), we don't have to install any software on the computer to remote access a edge device.

#### Todo
- [ ] Preview image size is too large
- [ ] Has an exception when run on X86
- [x] AGX tested

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

# [DeepCamera Feature List](docs/DeepCamera_Features.md)

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

## [How to install python3](https://www.python.org/downloads)
## [How to install pip3](https://pip.pypa.io/en/stable/installation)
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
