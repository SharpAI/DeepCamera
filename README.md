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
./setup.sh (rk3288 运行 ./setup_arm32.sh)
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


# 编译，打包

## 安装Pyinstaller
```
pip2 download pyinstaller
tar -xjvf PyInstaller-3.4.0.tar.bz2
cd PyInstaller-3.4.0
sed -i'' -e 's#"/usr/tmp"#"/data/data/com.termux/files/usr/tmp"#g' bootloader/src/pyi_utils.c
CFLAGS="-I/data/data/com.termux/files/usr/include/libandroid-support" LDFLAGS="-landroid-support" pip2 install .
```

## Build

```
cd build
bash ./build_aarch64.sh
```

## Run

```
cd build/runtime
bash ./start_aarch64.sh
```

## [移植过程](https://github.com/solderzzc/hotShare/issues/3239)


# SharpAI on Android ARM32(RK3288)

## Development

因为RK3288的data只有3G，需要加一个SD卡，一旦编译完毕，可以 tar 到备份SD卡，本地做删除，才有空间继续编译开发。

### Termux的执行环境（开发用）
#### usr_dev_root_1128_2018.tgz
#### 包含了除SVM之外的编译运行依赖，这是开发用的
链接:https://pan.baidu.com/s/1j41lNXYeYTruYsIXmo5YZA  密码:0yxx


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

## Runtime




 

