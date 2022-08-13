# Shinobi Motion Detector

Install required libraries.

**Ubuntu and Debian only**

```
sudo apt-get install libcairo2-dev libjpeg-dev libpango1.0-dev libgif-dev build-essential g++
```

**CentOS only**

```
su -c 'yum install cairo cairo-devel cairomm-devel libjpeg-turbo-devel pango pango-devel pangomm pangomm-devel giflib-devel'
yum search arial
yum install liberation-sans-fonts.noarch
```

**Install the Node.js Canvas engine**

```
sudo npm install canvas
```

Go to the Shinobi directory. **Below is an example.**

```
cd /home/Shinobi
```

Copy the config file.

```
cp plugins/motion/conf.sample.json plugins/motion/conf.json
```

Edit it the new file. Host should be `localhost` and port should match the `listening port for camera.js`.

```
nano plugins/motion/conf.json
```

Start the plugin.

```
node plugins/motion/shinobi-motion.js
```

Or to daemonize with PM2.

```
pm2 start plugins/motion/shinobi-motion.js
```

Doing this will reveal options in the monitor configuration. Shinobi does not need to be restarted when a plugin is initiated or stopped.

