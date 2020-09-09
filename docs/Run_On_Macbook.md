# Run on Macbook pro with iSight camera

To setup https://github.com/revmischa/rtsp-server

https://stackoverflow.com/questions/52682304/fatal-error-extern-h-file-not-found-while-installing-perl-modules/52997962


## you need to install ffmpeg on Macbook pro
## start rtsp server by following command line

On Macbook pro 2017, macOS Catalina 10.15.6
```
ffmpeg -f avfoundation -framerate 30 -video_size 1280x720 -i "0:none" -vcodec libx264 -preset ultrafast -tune zerolatency -pix_fmt uyvy422  -f mpegts udp://localhost:12345
```

```
curl -kL http://cpanmin.us | perl - App::cpanminus
```
