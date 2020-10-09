## Prepare Camera

Now you need to enable camera support using the raspi-config program you will have used when you first set up your Raspberry Pi. Use the cursor keys to select and open Interfacing Options, and then select Camera and follow the prompt to enable the camera.
https://www.raspberrypi.org/documentation/configuration/camera.md

## Prepare Docker
```
sudo curl -sSL https://get.docker.com | sh
```

## Start DeepCamera on Raspberry Pi 3/4

```
git clone https://github.com/SharpAI/DeepCamera
cd DeepCamera  
./run-on-rpi.sh start
```
