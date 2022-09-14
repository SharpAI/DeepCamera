https://github.com/theasp/docker-novnc

# noVNC Display Container
```
```
This image is intended to be used for displaying X11 applications from other containers in a browser. A stand-alone demo as well as a [Version 2](https://docs.docker.com/compose/compose-file/#version-2) composition.

## Image Contents

* [Xvfb](http://www.x.org/releases/X11R7.6/doc/man/man1/Xvfb.1.xhtml) - X11 in a virtual framebuffer
* [x11vnc](http://www.karlrunge.com/x11vnc/) - A VNC server that scrapes the above X11 server
* [noNVC](https://kanaka.github.io/noVNC/) - A HTML5 canvas vnc viewer
* [Fluxbox](http://www.fluxbox.org/) - a small window manager
* [xterm](http://invisible-island.net/xterm/) - to demo that it works
* [supervisord](http://supervisord.org) - to keep it all running

## Usage

### Variables

You can specify the following variables:
* `DISPLAY_WIDTH=<width>` (1024)
* `DISPLAY_HEIGHT=<height>` (768)
* `RUN_XTERM={yes|no}` (yes)
* `RUN_FLUXBOX={yes|no}` (yes)

### Stand-alone Demo
Run:
```bash
$ docker run --rm -it -p 8080:8080 theasp/novnc
```
Open a browser and see the `xterm` demo at `http://<server>:8080/vnc.html`

### V2 Composition
A version of the [V2 docker-compose example](https://github.com/theasp/docker/blob/master/docker-compose.yml) is shown below to illustrate how this image can be used to greatly simplify the use of X11 applications in other containers. With just `docker-compose up -d`, your favorite IDE can be accessed via a browser.

Some notable features:
* An `x11` network is defined to link the IDE and novnc containers
* The IDE `DISPLAY` environment variable is set using the novnc container name
* The screen size is adjustable to suit your preferences via environment variables
* The only exposed port is for HTTP browser connections

```
version: '2'
services:
  ide:
    image: psharkey/intellij:latest
#    image: psharkey/netbeans-8.1:latest
    environment:
      - DISPLAY=novnc:0.0
    depends_on:
      - novnc
    networks:
      - x11
  novnc:
    image: theasp/novnc:latest
    environment:
      # Adjust to your screen size
      - DISPLAY_WIDTH=1600
      - DISPLAY_HEIGHT=968
      - RUN_XTERM=no
    ports:
      - "8080:8080"
    networks:
      - x11
networks:
  x11:
```
**If the IDE fails to start simply run `docker-compose restart <container-name>`.**

## On DockerHub / GitHub
___
* DockerHub [theasp/novnc](https://hub.docker.com/r/theasp/novnc/)
* GitHub [theasp/docker/novnc](https://github.com/theasp/docker)

# Thanks
___
This is based on the alpine container by @psharkey: https://github.com/psharkey/docker/tree/master/novnc
Based on [wine-x11-novnc-docker](https://github.com/solarkennedy/wine-x11-novnc-docker) and [octave-x11-novnc-docker](https://hub.docker.com/r/epflsti/octave-x11-novnc-docker/).
