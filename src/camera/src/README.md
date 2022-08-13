# Shinobi Pro 
### (Creative Commons v4.0)

Shinobi is the Open Source CCTV Solution written in Node.JS. Designed with multiple account system, Streams by WebSocket, and Save to WebM. Shinobi can record IP Cameras and Local Cameras.

<a href="http://shinobi.video/gallery"><img src="https://github.com/ShinobiCCTV/Shinobi/blob/master/web/libs/img/demo.jpg?raw=true"></a>

# Key Aspects

For an updated list of features visit the official website. http://shinobi.video/features

- Time-lapse Viewer (Watch a hours worth of footage in a few minutes)
- 2-Factor Authentication
- Defeats stream limit imposed by browsers
  - With Base64 (Stream Type) and JPEG Mode (Option)
- Records IP Cameras and Local Cameras
- Streams by WebSocket, HLS (includes audio), and MJPEG
- Save to WebM and MP4
  - Can save Audio
- Push Events - When a video is finished it will appear in the dashboard without a refresh
- Region Motion Detection (Similar to ZoneMinder Zone Detection)
  - Represented by a Motion Guage on each monitor
- "No Motion" Notifications
- 1 Process for Each Camera to do both, Recording and Streaming
- Timeline for viewing Motion Events and Videos
- Sub-Accounts with permissions
  - Monitor Viewing
  - Monitor Editing
  - Video Deleting
  - Separate API keys for sub account
- Cron Filters can be set based on master account
- Stream Analyzer built-in (FFprobe GUI)
- Monitor Groups
- Can snapshot images from stream directly
- Lower Bandwith Mode (JPEG Mode)
  - Snapshot (cgi-bin) must be enabled in Monitor Settings
- Control Cameras from Interface
- API
  - Get videos
  - Get monitors
  - Change monitor modes : Disabled, Watch, Record
  - Embedding streams
- Dashboard Framework made with Google Material Design Lite, jQuery, and Bootstrap

## Asking for help

Before asking questions it would nice if you read the docs :) http://shinobi.video

After doing so please head on over to the Discord community chat for support. https://discordapp.com/invite/mdhmvuH

The Issues section is only for bugs with the software. Comments and feature requests may be closed without comment. http://shinobi.video/docs/contribute

Please be considerate of developer efforts. If you have simple questions, like "what does this button do?", please be sure to have read the docs entirely before asking. If you would like to skip reading the docs and ask away you can order a support package :) http://shinobi.video/support

## Making Suggestions or Feature Requests

You can post suggestions on the Forum in the Suggestions category. Please do not treat this channel like a "demands" window. Developer efforts are limited. Much more than many alternatives.

when you have a suggestion please try and make the changes yourself then post a pull request to the `dev` branch. Then we can decide if it's a good change for Shinobi. If you don't know how to go about it and want to have me put it higher on my priority list you can order a support package :) Pretty Ferengi of me... but until we live in a world without money please support Shinobi :) Cheers!

http://shinobi.video/support

## Help make Shinobi the best Open Source CCTV Solution.
Donate - http://shinobi.video/docs/donate

Ordering a License, Paid Support, or anything from <a href="//camera.observer">here</a> will allow a lot more time to be spent on Shinobi.

Order Support - http://shinobi.video/support

# Why make this?

http://shinobi.video/why

# What others say

> "After trying zoneminder without success (heavy unstable and slow) I passed to Shinobi that despite being young spins a thousand times better (I have a setup with 16 cameras recording in FHD to ~ 10fps on a pentium of ~ 2009 and I turn with load below 1.5)."

> *A Reddit user, /r/ItalyInformatica*

&nbsp;

> "I would suggest Shinobi as a NVR. It's still in the early days but works a lot better than ZoneMinder for me. I'm able to record 16 cams at 1080p 15fps continously whith no load on server (Pentium E5500 3GB RAM) where zm crashed with 6 cams at 720p. Not to mention the better interface."

> *A Reddit user, /r/HomeNetworking*

# How to Install and Run

> FOR DOCKER USERS : Docker is not officially supported and is not recommended. The kitematic method is provided for those who wish to quickly test Shinobi. The Docker files included in the master and dev branches are maintained by the community. If you would like support with Docker please find a community member who maintains the Docker files or please refer to Docker's forum.

#### Fast Install (The Ninja Way)

1. Become `root` to use the installer and run Shinobi. Use one of the following to do so.

    - Ubuntu 17.04, 17.10
        - `sudo su`
    - CentOS 7
        - `su`
    - MacOS 10.7(+)
        - `su`
2. Download and run the installer.

```
bash <(curl -s https://raw.githubusercontent.com/ShinobiCCTV/Shinobi-Installer/master/shinobi-install.sh)
```

#### Elaborate Installs

Installation Tutorials - http://shinobi.video/docs/start

Troubleshooting Guide - http://shinobi.video/docs/start#trouble-section

# Author

Moe Alam

Follow Shinobi on Twitter https://twitter.com/ShinobiCCTV

Join the Community Chat

<a title="Find me on Discord, Get an Invite" href="https://discordapp.com/invite/mdhmvuH"><img src="https://cdn-images-1.medium.com/max/115/1*OoXboCzk0gYvTNwNnV4S9A@2x.png"></a>

# Support the Development

Ordering a certificate or support package greatly boosts development. Please consider contributing :)

http://shinobi.video/support

# Links

Documentation - http://shinobi.video/docs

Donate - https://shinobi.video/docs/donate

Tested Cameras and Systems - http://shinobi.video/docs/supported

Features - http://shinobi.video/features

Reddit (Forum) - https://www.reddit.com/r/ShinobiCCTV/

YouTube (Tutorials) - https://www.youtube.com/channel/UCbgbBLTK-koTyjOmOxA9msQ

Discord (Community Chat) - https://discordapp.com/invite/mdhmvuH

Twitter (News) - https://twitter.com/ShinobiCCTV

Facebook (News) - https://www.facebook.com/Shinobi-1223193167773738/?ref=bookmarks