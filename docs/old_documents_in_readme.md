

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

baidu cloud

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
git clone https://github.com/SharpAI/DeepCamera
cd DeepCamera
```

#### AArch64 (RK3399/7420 ...)
```
./setup.sh
```

#### Arm32 (RK3288)
```
./setup_arm32.sh
```


### Start Service
```
./start_service.sh
```

## RTSP Input

Use RTSP Decoder

# Compile，Package

## Install Pyinstaller
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

only 3G data space for Rk3288，need an extra SD card，can be backup to SD card after compiling for more space.

### developing environment of Termux
#### usr_dev_root_1128_2018.tgz
#### including all libraries for development except SVM.
link:https://pan.baidu.com/s/1MjlCUiiUVf0z_ILoZ7y44w  password:3rh7

for more space：
```
pkg uninstall gcc-6 gcc-7 gcc-8
```

Use sharpai/build/build_arm.sh to Build

### Developing environment on Arch Linux
#### arch_dev_root.tgz
#### scikit-learn(SVM) only works on ARCH Linux

link:https://pan.baidu.com/s/1TJzKemhjfk_CWqbxaz7nvw  password:b5cg

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

## running environment after packaging（for release）

### Termux Runtime:    runtime_termux_armv7.tgz


link:https://pan.baidu.com/s/136d1nVtPfQrrxqCZWjebLA  password:5e53

### Built Application
link:https://pan.baidu.com/s/1x71O1npURpMvQCv-jQ4Fwg  password:qyex
```
cd ~
tar -zxvf runtime_all_armv7.tgz
```

### Arch Linux Runtime: runtime_arch_linux_armv7.tgz
link:https://pan.baidu.com/s/16ta4yC_mp6AOrhMyCs6N0w  password:xwdr

```
cd ~
tar -zxvf runtime_arch_linux_armv7.tgz

wget https://sdrausty.github.io/TermuxArch/setupTermuxArch.sh
bash setupTermuxArch.sh
```


```
./arch/startarch c "cd /data/data/com.termux/files/home/runtime_arch/bin && ./classifier "

```
