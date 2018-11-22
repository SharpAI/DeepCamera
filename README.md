# SharpAI On Android AARCH64

## 1. Download Termux Modified Version on PC

```
git clone https://github.com/solderzzc/hotShare -b android_porting
```

## 2. Add authorized key

Copy your pc ~/.ssh/id_rsa.pub to android ~/.ssh/authorized_keys (using ssh to connect android device)

AndroidPorting/Launcher/app/src/main/assets/authorized_keys

## 3. Setup on Android

```
pkg install openssh
sshd
```

## 4. Then Remote access it for easy

```
ssh -p 8022 username@192.168.x.x
```

## 5. Install Base Root File System

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


## 6. Run Sharp AI Code

### 下载代码
```
git clone https://github.com/solderzzc/sharpai
cd sharpai
./setup.sh
```


### 运行服务
```
./start_service.sh
```

## RTSP 输入源

https://github.com/solderzzc/hotShare/tree/android_porting/AndroidPorting/vlc-example-streamplayer

修改地址：
https://github.com/solderzzc/hotShare/blob/android_porting/AndroidPorting/vlc-example-streamplayer/app/src/main/java/com/pedro/vlctestapp/MainActivity.java#L173

然后运行
直接点Play



## [移植过程](https://github.com/solderzzc/hotShare/issues/3239)


# RK3288 的使用方法

链接:https://pan.baidu.com/s/13A6wI0Nt-BnlPKdEmu242w  密码:3swc


