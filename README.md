# What's SharpAI
Full stack system for the deep learning edge computing devices, espeicailly set-up-box off the shell with image burning or Android apk installation.

# Feature List
- [x] Hige accurate Face Recognition
- [x] Face Detection
- [x] Infrence on ARM Mali GPU
- [x] Support Android TF Lite(GPU/CPU/NPU)
- [x] Support open source embedded linux
- [x] Control from mobile application
- [x] Management System for devices
- [x] Push Notification to Mobile Device
- [x] Object Detection
- [x] Distributed System based on celery
- [x] Plugin to process video by Shinobi CCTV
- [x] Application on Android to decode video with hw acc
- [x] Motion Detection with Android GPU
- [x] Lable and train from Mobile to Edge Device

# Supported Device
- [x] X86
- [x] Rockchip RK3399 (Linux)
- [x] Rockchip RK3288 (Android)
- [x] Samsung 7420 (Android)
- [x] Rockchip RK3399 (Android)

# Supported Camera
- [x] Dahua Camera
- [x] Hikvision Camera
- [x] Shinobi CCTV Supported Devices
- [x] Screen Captured from Android Camera preview application

![screen shot 2019-03-07 at 4 03 59 pm](https://user-images.githubusercontent.com/3085564/53941268-a0781b80-40f2-11e9-8cc6-6295c3a39c96.png)

![screen shot 2019-03-07 at 2 41 28 pm](https://user-images.githubusercontent.com/3085564/53937113-1a0a0c80-40e7-11e9-96d6-1ab215c7db72.png)

![screen shot 2019-03-07 at 11 27 22 am](https://user-images.githubusercontent.com/3085564/53930362-fdaca680-40cb-11e9-8303-d538315d9021.png)

![screen shot 2019-03-07 at 11 30 54 am](https://user-images.githubusercontent.com/3085564/53930505-7c094880-40cc-11e9-939a-1368cc557a0c.png)

# How to test on PC
```
git clone https://github.com/SharpAI/sharpai
cd sharpai/docker
docker-compose -f docker-compose-x86.yml up
```

# [Runtime On AARCH64](docs/Runtime_AARCH64.md)


# SharpAI On Android AARCH64

## 1. Download Termux Modified Version on PC

```
git clone https://github.com/SharpAI/mobile_app_server -b android_porting
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

百度云盘

`uploading`

```
scp -P 8022 usr_aarch64_dev_1204_2018.tgz a@192.168.x.x:/data/data/com.termux/files/
```

### On Android
```
cd /data/data/com.termux/files
tar -xvf usr_aarch64_dev_1204_2018.tgz
```


## 6. Run Sharp AI Code

### Download Source Code
```
git clone https://github.com/SharpAI/sharpai
cd sharpai
./setup.sh (rk3288 运行 ./setup_arm32.sh)
```


### Start Service
```
./start_service.sh
```

## RTSP Input

Use RTSP Decoder

# 编译，打包

## 安装Pyinstaller
```
pip2 download pyinstaller
tar -xjvf PyInstaller-3.4.tar.bz2
cd PyInstaller-3.4
sed -i'' -e 's#"/usr/tmp"#"/data/data/com.termux/files/usr/tmp"#g' bootloader/src/pyi_utils.c
CFLAGS="-I/data/data/com.termux/files/usr/include/libandroid-support" LDFLAGS="-landroid-support" pip2 install .
```

## Build

```
cd build
bash ./build_aarch64.sh runtime's path
```

## Run

```
cd [runtime full path]/runtime
bash ./start_aarch64.sh
```

# SharpAI on Android ARM32(RK3288)

## Development

因为RK3288的data只有3G，需要加一个SD卡，一旦编译完毕，可以 tar 到备份SD卡，本地做删除，才有空间继续编译开发。

### Termux的执行环境（开发用）
#### usr_dev_root_1128_2018.tgz
#### 包含了除SVM之外的编译运行依赖，这是开发用的
链接:https://pan.baidu.com/s/1MjlCUiiUVf0z_ILoZ7y44w  密码:3rh7

空间不够了，这样节省一些：
```
pkg uninstall gcc-6 gcc-7 gcc-8
```

Use sharpai/build/build_arm.sh to Build

### Arch Linux的执行环境（开发用）
#### arch_dev_root.tgz
#### ARCH Linux才能够正常使用scikit-learn(SVM),原因没查出来

链接:https://pan.baidu.com/s/1TJzKemhjfk_CWqbxaz7nvw  密码:b5cg

```
cd ~
tar -zxvf arch_dev_root.tgz

wget https://sdrausty.github.io/TermuxArch/setupTermuxArch.sh
bash setupTermuxArch.sh
```
```
./arch/startarch
```
Use `sharpai/build/build_arm_svc.sh` to Build

## 打包后的程序运行环境（产品发布用）

### Termux Runtime:    runtime_termux_armv7.tgz


链接:https://pan.baidu.com/s/136d1nVtPfQrrxqCZWjebLA  密码:5e53

### 编译后的可执行程序
链接:https://pan.baidu.com/s/1x71O1npURpMvQCv-jQ4Fwg  密码:qyex
```
cd ~
tar -zxvf runtime_all_armv7.tgz
```

### Arch Linux Runtime: runtime_arch_linux_armv7.tgz
链接:https://pan.baidu.com/s/16ta4yC_mp6AOrhMyCs6N0w  密码:xwdr

```
cd ~
tar -zxvf runtime_arch_linux_armv7.tgz

wget https://sdrausty.github.io/TermuxArch/setupTermuxArch.sh
bash setupTermuxArch.sh
```


```
./arch/startarch c "cd /data/data/com.termux/files/home/runtime_arch/bin && ./classifier "

```
 

