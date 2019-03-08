# RK3288 Source Code（For Face Recognition）

## 1 Prepare rk3288 Environment（Connect dev box and workstation in the same network）

### 1-1 get modified termux apk (Built from [here](https://github.com/SharpAI/mobile_app_server/tree/android_porting/AndroidPorting/Launcher))

#### 1-1-1 From Baidu (sharpai-norootfs-lambda_key.apk)
> Link: https://pan.baidu.com/s/1ic3jEItCNG8mgJQPlHBYhg Password: mq9p
#### 1-1-2 termux Compile
> Use Android studio to build https://github.com/SharpAI/mobile_app_server/tree/android_porting/AndroidPorting/Launcher

### 1-2 Install modified termux apk
#### 1-2-1 from u disk
> Connect Udisk into RK3288 Android 5.1, then install

#### 1-2-2 from adb 
```
adb install sharpai-norootfs-lambda_key.apk
```

### 1-3 install openssh termux 

```
$ pkg install openssh
```
Start ssh
```
$ sshd
```

Connect to RK3288 through IP
```
$ ssh -p 8022 xxx.xxx.xxx.xxx

```


#### c. Update apt source of termux to ensure the installation of graphicsmagick
```
$ rm -rf /data/data/com.termux/files/usr/var/lib/apt/*
$ apt-get update
```


### 1-2 Install Source Code 
Download based root fs and arch linux fs

>usr_dev_root_armv7_1126_2018.tgz
link: https://pan.baidu.com/s/18GwmAj04ylqg1AYS5T5BQA password:0w8a
arch_dev_root_1203_2018_final.tgz
link: https://pan.baidu.com/s/1FdaTiqjuLKEr7ZvKw2JF4g password:hvlz

Upload them onto RK3288 box
```
$ cd /data/data/com.termux/files/
$ scp lambda@ip:/data/usr_dev_root_armv7_1126_2018.tgz .
$ tar -zxvmf usr_dev_root_armv7_1126_2018.tgz
$ rm -f usr_dev_root_armv7_1126_2018.tgz
$ cd /data/data/com.termux/files/home
$ scp lambda@ip:/data/arch_dev_root_1203_2018_final.tgz .
$ tar -zxvmf arch_dev_root_1203_2018_final.tgz
$ rm -f arch_dev_root_1203_2018_final.tgz
```
Also you can use adb push
> reference https://developer.android.com/studio/command-line/adb?hl=en-us

## 2 Prepare source code runtime
```
$ cd /data/data/com.termux/files/home
$ git clone https://github.com/SharpAI/DeepCamera
```

For ReID（Only if needed）
$ cd /data/data/com.termux/files/home/sharpai
$ git checkout origin/human_master_rk3399_linux -b human_master_rk3399_linux  
```

For ReID
Download model model-armv7a.tgz
> Link: https://pan.baidu.com/s/1ic3jEItCNG8mgJQPlHBYhg password: mq9p

upload, untar, remove
```
$ cd /data/data/com.termux/files/home/sharpai
$ tar -zxvmf model-rk3288-termux.tgz
$ rm -f model-rk3288-termux.tgz
```



Install must have dependencies
```
$ pip2 uninstall scipy
$ apt-get install python2-scipy

$ apt-get install graphicsmagick

$ cd /data/data/com.termux/files/home/sharpai/src/flower/
$ pip2 install -r requirements.txt

$ cd /data/data/com.termux/files/home/sharpai/src/detector/
$ npm install
```


## 3 Start
```
$ cd /data/data/com.termux/files/home/sharpai
$ ./start_service_arm32.sh
```

> Fixed for runtime error
Add following line to files:
```
# -*-coding:UTF-8 -*-
```
files：
>/data/data/com.termux/files/usr/lib/python2.7/site-packages/scipy-1.2.0-py2.7-linux-armv8l.egg/scipy/stats/_continuous_distns.py
/data/data/com.termux/files/usr/lib/python2.7/site-packages/scipy-1.2.0-py2.7-linux-armv8l.egg/scipy/stats/_stats_mstats_common.py
