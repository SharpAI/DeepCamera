# Intrusion detection AI camera with Home-Assistant

DeepCamera empowers your traditional surveillance cameras and CCTV/NVR with machine learning technologies. 
It provides open source facial recognition based intrusion detection, fall detection and parking lot monitoring with the inference engine on your local device.

SharpAI-hub is the cloud hosting for AI applications which help you deploy AI applications with your CCTV camera on your edge device in minutes. 

# Install SharpAI-Hub CLI
Support Jetson Nano/Xavier AGX/Windows/Linux/MacOS
- Register account on [SharpAI website](http://dp.sharpai.org:3000)
- Install sharpai-hub: `pip3 install sharpai-hub`
- Login on device: `sharpai-cli login`
- Register device: `sharpai-cli device register`

# Start DeepCamera
### 1. Start DeepCamera
```
sharpai-cli deepcamera start
```
### 2. Land-on Home-Assistant with URL: http://localhost:8123
### 3. Add your Camera through Home-Assistant camera integration
### 4. Added SharpAI configuration to configuration.yaml
```
stream:
  ll_hls: true
  part_duration: 0.75
  segment_duration: 6

image_processing:
  - platform: sharpai
    source:
      - entity_id: camera.<camera_entity_id>
    scan_interval: 1
```
### 5. Access detection result on [SharpAI website](http://dp.sharpai.org:3000)
### 6. Integration with Home-Assistant
### 7. [Implementation detail](docs/DeepCamera_introduction.md)

## Local deployment is ready for testing now

Since the most concern from community is security/privacy, we implemented local deployment by sharpai-cli command line.
```
sharpai-cli local_deepcamera start
```
It will bring up everything on you own machine, so after the setup, you can disconnect your machine from internet and it will still work.
This release is supporting x86 machine.
When you have everything running, the GUI will be here: [http://localhost:3000](http://localhost:3000)

# Other Applications(early release)
- [Parking lot protection](docs/Yolo_Parking.md)
- [Fall Detection](docs/FallDetection_with_shinobi.md)

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
- If you are using a camera but have no idea about the RTSP URL, please join SharpAI community for help.
- SharpAI provides commercial support to companies which want to deploy AI Camera application to real world.
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
