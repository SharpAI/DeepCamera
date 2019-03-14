# Run On Android(AArch64)

## Get Launcher_Termux source code
```
git clone https://github.com/SharpAI/Launcher_Termux
```

## Config authorized_keys for ssh
Open Launcher_Termux, add your id_rsa.pub in authorized_keys

![add authorized keys](../screenshots/add_authorized_keys.png)

## Launch Launcher_Termux in Android Studio

## Install openssh in Launcher_Termux

```
pkg install openssh
sshd
```

## Remote access to Launcher_Termux through ssh

```
ssh -p 8022 a@Android_IP
```

## Install development rootfs(Launcher_Termux ssh environment)

```
pkg update
pkg install wget
cd /data/data/com.termux/files
wget https://github.com/SharpAI/DeepCamera/releases/download/1.1/usr_aarch64_dev_1204_2018.tgz
tar -zxf usr_aarch64_dev_1204_2018.tgz
```
#### you can delete usr_aarch64_dev_1204_2018.tgz to save space or just keep it

## Test if working

### Following works on Rockpro64 Android 7.1.2, please report issue if you have runtime warning
```
LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$PREFIX/lib64:/system/lib64:/system/vendor/lib64/egl:/system/vendor/lib64 LD_PRELOAD=$LD_PRELOAD:/system/lib64/libcrypto.so:/system/lib64/libcompiler_rt.so python2

import tvm
import mxnet
```
```
>>> tvm.__version__
'0.5.dev'
>>> mxnet.__version__
'0.10.1'
```

## Get the source code of DeepCamera
```
mkdir ~/build
git clone https://github.com/SharpAI/DeepCamera
cd DeepCamera
./setup.sh
cd build
./build_aarch64.sh ~/build/
```
