# SharpAI On Android

## Download Termux Modified Version on PC

```
git clone https://github.com/solderzzc/hotShare -b android_porting
```

## Add authorized key

AndroidPorting/Launcher/app/src/main/assets/authorized_keys

## Build and run it

## Setup

```
pkg install openssh
sshd
```

## Then Remote access it for easy

```
ssh -p 8022 a@192.168.x.x
```

## Install Base Root File System

### ON PC
```
wget https://github.com/solderzzc/model_release/releases/download/v1.0/usr_10312018.tgz
scp -P 8022 usr_10312018.tgz a@192.168.x.x:/data/data/com.termux/files/
```
or 百度云盘

链接: https://pan.baidu.com/s/1hG6z2BdXCy82xtjXu3mrZg 提取码: 54cp

### On Android
```
cd /data/data/com.termux/files
tar -xvf usr_10312018.tgz 
```

## Restart TERMUX

## Run Sharp AI Code

```
git clone https://github.com/solderzzc/sharpai
cd sharpai
./setup.sh
./start_service.sh
```

## RTSP 输入源

https://github.com/solderzzc/hotShare/tree/android_porting/AndroidPorting/vlc-example-streamplayer

修改地址：
https://github.com/solderzzc/hotShare/blob/android_porting/AndroidPorting/vlc-example-streamplayer/app/src/main/java/com/pedro/vlctestapp/MainActivity.java#L173

然后运行
直接点Play



## [移植过程](https://github.com/solderzzc/hotShare/issues/3239)
