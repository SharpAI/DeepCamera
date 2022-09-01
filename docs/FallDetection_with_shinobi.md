
# Fall Detection
Using Tiny-YOLO oneclass to detect each person in the frame and use AlphaPose to get skeleton-pose and then use ST-GCN model to predict action from every 30 frames of each person tracks. [Github Link](https://github.com/SharpAI/FallDetection)
```
sharpai-cli falldetection start
```

#### Linux Desktop GUI is accessible through http://localhost:8000, thanks to open source web vnc client [noVNC](https://novnc.com/info.html), we don't have to install any software on the computer to remote access a edge device.

#### Todo
- [ ] Integrate with Home-Assistant
- [x] AGX tested

# Connect RTSP camera source to built-in Shinobi CCTV/NVR
You need to get the RTSP url of your camera and add it to NVR. Then NVR engine will pull video stream through RTSP protocol from your camera, after extracting frame from video stream, the extracted frame will be sent to detector for AI tasks.

- Built-in Shinobi CCTV/NVR GUI address: http://localhost:8080   
