#!/bin/tcsh
echo "========================================================="
echo "==== Shinobi : The Open Source CCTV and NVR Solution ===="
echo "========================================================="
echo "This script should run as root inside your jail from the root"
echo "of the cloned git repository."
echo "To answer yes type the letter (y) in lowercase and press ENTER."
echo "Default is no (N). Skip any components you already have or don't need."
echo "============="
echo "Shinobi - Do you want to Install Node.js?"
echo "(y)es or (N)o"
set nodejsinstall = $<
if ( $nodejsinstall == "y" ) then
	pkg install -y node8 npm-node8
endif
echo "============="
echo "Shinobi - Do you want to Install FFMPEG?"
echo "(y)es or (N)o"
set ffmpeginstall = $<
if ( $ffmpeginstall == "y" ) then
	pkg install -y ffmpeg libav x264 x265
endif
echo "============="
echo "Shinobi - Database Installation"
echo "WARNING - This requires an existing and running mariadb service."
echo "(y)es or (N)o"
set mysqlagreeData = $<
if ( $mysqlagreeData == "y" ) then
    echo "What is your SQL Username?"
    set sqluser = $<
    echo "What is your SQL Password?"
    set sqlpass = $<
    echo "What is your SQL Host?"
    set sqlhost = $<
    echo "Installing mariadb client..."
    pkg install -y mariadb102-client
    echo "Installing database schema..."
    mysql -h $sqlhost -u $sqluser -p$sqlpass -e "source sql/user.sql" || true
    mysql -h $sqlhost -u $sqluser -p$sqlpass -e "source sql/framework.sql" || true
    echo "Shinobi - Use the /super endpoint to create your super user."
endif
echo "============="
echo "Shinobi - Install NPM Libraries"
npm install
echo "============="
echo "Shinobi - Install PM2"
npm install pm2 -g
if (! -e "./conf.json" ) then
    cp conf.sample.json conf.json
endif
if (! -e "./super.json" ) then
    echo "Default Superuser : admin@shinobi.video"
    echo "Default Password  : admin"
    cp super.sample.json super.json
endif
echo "Shinobi - Start Shinobi?"
echo "(y)es or (N)o"
set startShinobi = $<
if ( $startShinobi == "y" ) then
    set PM2BIN="$PWD/node_modules/pm2/bin"
    $PM2BIN/pm2 start camera.js
    $PM2BIN/pm2 start cron.js
    $PM2BIN/pm2 save
    $PM2BIN/pm2 list
endif
echo "Shinobi - Start on boot?"
echo "(y)es or (N)o"
set startupShinobi = $<
if ( $startupShinobi == "y" ) then
    set PM2BIN="$PWD/node_modules/pm2/bin"
    $PM2BIN/pm2 startup rcd
endif
echo "Shinobi - Finished"
