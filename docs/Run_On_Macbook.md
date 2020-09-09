# Run on Macbook pro with iSight camera

To setup https://github.com/revmischa/rtsp-server

https://stackoverflow.com/questions/52682304/fatal-error-extern-h-file-not-found-while-installing-perl-modules/52997962

The best practice seems to be starting with a Perl using brew install perl and work in this environment, remembering to setup your bash_profile as directed by the installer.

Also worth remembering to do a brew link perl. If you receive warnings about this clobbering what looks like system Perl libraries don't worry - these are likely modules that were installed by you over the top and it will cause you less trouble to link over these. If you have concerns, make a note of which module installs will be cleared and re-install them once your environment is configured ( ie your module installer approach is configured using cpanm or sticking with the old perl -MCPAN -e shell etc)

This new Perl setup from brew eliminates the need to continuing running sudo which adds another layer of things that can go wrong as environment variables don't follow through and permission conflicts arise etc.

Finally to simplify package/module installation I suggest doing a brew install cpanminus. If you had previously already installed this, you can ensure the paths etc are configured by doing a brew reinstall cpanminus


## you need to install ffmpeg on Macbook pro
## start rtsp server by following command line

On Macbook pro 2017, macOS Catalina 10.15.6
```
ffmpeg -f avfoundation -framerate 30 -video_size 1280x720 -i "0:none" -vcodec libx264 -preset ultrafast -tune zerolatency -pix_fmt uyvy422  -f mpegts udp://localhost:12345
```

```
curl -kL http://cpanmin.us | perl - App::cpanminus
```
