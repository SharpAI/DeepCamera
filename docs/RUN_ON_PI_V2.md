## Prepare System
Summary(conversation on [slack](https://sharpai-invite-automation.herokuapp.com/)):

1. works out of box if you have 8GB memory version of Raspberry-pi.
2. you need at least 4GB memory version of Raspberry-Pi, please add 2GB swap to run services.
3. if you got HTTP request error, please restart services several times.
4. Please install 32bit system (official raspbian works)

## Prepare Camera

Now you need to enable camera support using the raspi-config program you will have used when you first set up your Raspberry Pi. Use the cursor keys to select and open Interfacing Options, and then select Camera and follow the prompt to enable the camera.
https://www.raspberrypi.org/documentation/configuration/camera.md

## Prepare Docker
```
sudo curl -sSL https://get.docker.com | sh
```

## on PC/Server/Cloud
```
git clone https://github.com/SharpAI/DeepCamera
cd DeepCamera
./start-cloud.sh start
```
You need ip address of private cloud server on next step (replace ip address to <Server_IP> on next step)

## on Raspberry Pi 3/4

### Get source code
```
git clone https://github.com/SharpAI/DeepCamera
```

### Configure

edit configuration on Pi, change following environment var to 1's ip address:

#### [aws.env](../docker/aws.env)
AWS_END_POINT='<Server_IP>'  
AWS_READABLE_PREFIX='http://<Server_IP>:9000/storage/'

#### [servers.env](../docker/servers.env)
MQTT_BROKER_ADDRESS=<Server_IP>  
API_SERVER_ADDRESS=<Server_IP>
### Start DeepCamera
```
git clone https://github.com/SharpAI/DeepCamera
cd DeepCamera  
./run-on-rpi.sh start
```
