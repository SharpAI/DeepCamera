#!/bin/bash
echo "========================================================="
echo "==!! Shinobi : The Open Source CCTV and NVR Solution !!=="
echo "=================== Mac OS Install Part 1 ==============="
echo "========================================================="
echo "To answer yes type the letter (y) in lowercase and press ENTER."
echo "Default is no (N). Skip any components you already have or don't need."
echo "============="
echo "Shinobi - Do you want to Install Node.js?"
echo "(y)es or (N)o"
read nodejsinstall
if [ "$nodejsinstall" = "y" ]; then
    curl -o node-v8.9.3.pkg https://nodejs.org/dist/v8.9.3/node-v8.9.3.pkg
    sudo installer -pkg node-v8.9.3.pkg -target /
    rm node-v8.9.3.pkg
    sudo ln -s /usr/local/bin/node /usr/bin/nodejs
fi
echo "============="
echo "Shinobi - Do you want to Install FFmpeg?"
echo "(y)es or (N)o"
read ffmpeginstall
if [ "$ffmpeginstall" = "y" ]; then
    echo "Shinobi - Installing FFmpeg"
    curl -o ffmpeg.zip https://cdn.shinobi.video/installers/ffmpeg-3.4.1-macos.zip
    sudo unzip ffmpeg.zip
    sudo rm ffmpeg.zip
    sudo mv ffmpeg-3.4.1-macos/ffmpeg /usr/bin/ffmpeg
    sudo mv ffmpeg-3.4.1-macos/ffplay /usr/bin/ffplay
    sudo mv ffmpeg-3.4.1-macos/ffprobe /usr/bin/ffprobe
    sudo mv ffmpeg-3.4.1-macos/ffserver /usr/bin/ffserver
    sudo chmod +x /usr/bin/ffmpeg
    sudo chmod +x /usr/bin/ffplay
    sudo chmod +x /usr/bin/ffprobe
    sudo chmod +x /usr/bin/ffserver
fi
echo "============="
echo "Shinobi - Do you want to Install MySQL? Choose No if you have MySQL or MySQL already."
echo "(y)es or (N)o"
read mysqlagree
if [ "$mysqlagree" = "y" ]; then
    echo "Shinobi - Installing MySQL"
    bash <(curl -Ls http://git.io/eUx7rg)
fi
echo "============="
echo "============="
echo "You must now close this terminal window and reopen it."
echo "Reopen the Shinobi folder and run"
echo "chmod +x INSTALL/macos-part2.sh && INSTALL/macos-part2.sh"
echo "============="
echo "============="