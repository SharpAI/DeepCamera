# OpenALPR and Motion Detector

Install required libraries.

**Ubuntu and Debian only**

```
sudo apt update && sudo apt install libcairo2-dev libjpeg-dev libpango1.0-dev libgif-dev build-essential g++ openalpr openalpr-daemon openalpr-utils libopenalpr-dev -y
```

**Install the Node.js Canvas engine**

```
sudo npm install canvas@1.6
```
Go to the Shinobi directory. **Below is an example.**

```
cd /home/Shinobi
```

Copy the config file.

```
cp plugins/openalpr/conf.sample.json plugins/openalpr/conf.json
```

Edit it the new file. Host should be `localhost` and port should match the `listening port for camera.js`.

```
nano plugins/openalpr/conf.json
```

Start the plugin.

```
node plugins/openalpr/shinobi-motion.js
```

Or to daemonize with PM2.

```
pm2 start plugins/openalpr/shinobi-motion.js
```

Doing this will reveal options in the monitor configuration. Shinobi does not need to be restarted when a plugin is initiated or stopped.

## Run the plugin as a Host
> The main app (Shinobi) will be the client and the plugin will be the host. The purpose of allowing this method is so that you can use one plugin for multiple Shinobi instances. Allowing you to easily manage connections without starting multiple processes.

Edit your plugins configuration file. Set the `hostPort` **to be different** than the `listening port for camera.js`.

```
nano plugins/openalpr/conf.json
```

Here is a sample of a Host configuration for the plugin.
 - `plug` is the name of the plugin corresponding in the main configuration file.
 - `https` choose if you want to use SSL or not. Default is `false`.
 - `hostPort` can be any available port number. **Don't make this the same port number as Shinobi.** Default is `8082`.
 - `type` tells the main application (Shinobi) what kind of plugin it is. In this case it is a detector.

```
{
  "plug":"OpenALPR",
  "hostPort":8082,
  "key":"SomeOpenALPRkeySoPeopleDontMessWithYourShinobi",
  "mode":"host",
  "type":"detector"
}
```

Now modify the **main configuration file** located in the main directory of Shinobi. *Where you currently should be.*

```
nano conf.json
```

Add the `plugins` array if you don't already have it. Add the following *object inside the array*.

```
  "plugins":[
      {
          "id" : "OpenALPR",
          "https" : false,
          "host" : "localhost",
          "port" : 8082,
          "key" : "SomeOpenALPRkeySoPeopleDontMessWithYourShinobi",
          "mode" : "host",
          "type" : "detector"
      }
  ],
```