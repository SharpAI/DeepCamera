# DeepCamera on RK3288

## 1 Prepare RK3288 Environment（Connect dev box and workstation in the same network）

### 1-1 Install SharpAI LauncherTermux

#### 1-1-1 [SharpAI-LauncherTermux.apk](https://github.com/SharpAI/DeepCamera/releases/download/1.1/SharpAI-LauncherTermux.apk)
#### 1-1-2 [Source Code](https://github.com/SharpAI/Launcher_Termux)

### 1-2 Install modified termux apk
#### 1-2-1 from u disk
> Connect Udisk into RK3288 Android 5.1, then install

#### 1-2-2 from adb 

The following figure：

![image.png](https://cdn.nlark.com/yuque/0/2019/png/170897/1552229210075-a6ab9acf-76b9-4bf4-82d5-45bd4a492622.png)

```
adb install SharpAI-LauncherTermux.apk
```

#### 1-2-3 install openssh termux 

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

If SSH connection fails, need to put the public key content appended to the box on the local computer.

~/.ssh/id_rsa.pub >> data/data/com.termux/files/home/.ssh/authorized_keys.

Refer to the link：[https://www.jianshu.com/p/2e6c8152a2ba](https://www.jianshu.com/p/2e6c8152a2ba)

```

adb root

adb push ~/.ssh/id_rsa.pub /data/data/com.termux/files/home/.ssh/id_rsa.pub

adb shell

cd data/data/com.termux/files/home/.ssh/

cat ./id_rsa.pub >> authorized_keys
```


#### 1-2-4 Update apt source of ssh to ensure the installation of graphicsmagick
```

$ rm -rf /data/data/com.termux/files/usr/var/lib/apt/*
$ apt-get update

```


### 1-3 Install Source Code 

```
pkg install wget
cd /data/data/com.termux/files/
$PRIFIX/bin/wget https://github.com/SharpAI/DeepCamera/releases/download/1.1/usr_dev_root_armv7_1126_2018.tgz
tar -zxmf usr_dev_root_armv7_1126_2018.tgz
```

##### Remove if you want to save space
```
rm -f usr_dev_root_armv7_1126_2018.tgz
```

```
cd /data/data/com.termux/files/home
$PRIFIX/bin/wget https://github.com/SharpAI/DeepCamera/releases/download/1.1/arch_dev_root_1203_2018_final.tgz
tar -zxmf arch_dev_root_1203_2018_final.tgz
```

##### Remove if you want to save space
```
rm -f arch_dev_root_1203_2018_final.tgz
```


## 2 Prepare source code runtime
```
$ cd /data/data/com.termux/files/home
$ git clone https://github.com/SharpAI/DeepCamera
cd DeepCamera
./setup_arm32.sh
```

Install must have dependencies
```
$ apt-get install graphicsmagick
```


## 3 Start
```
$ cd /data/data/com.termux/files/home/DeepCamera
$ ./start_service_arm32.sh
```


```
LD_LIBRARY_PATH=/system/lib:$LD_LIBRARY_PATH:$PREFIX/lib:/system/vendor/lib/egl:/system/vendor/lib LD_PRELOAD=$LD_PRELOAD:libatomic.so:libcutils.so python2

import tvm
```
