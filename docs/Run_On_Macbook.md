# Run on Macbook pro with iSight camera

## you need to install ffmpeg on Macbook pro
## start rtsp server by following command line

On Macbook pro 2017, macOS Catalina 10.15.6
```
ffmpeg -f avfoundation -framerate 30 -video_size 1280x720 -i "0:none" -vcodec libx264 -preset ultrafast -tune zerolatency -pix_fmt uyvy422  -f mpegts udp://localhost:12345
```
