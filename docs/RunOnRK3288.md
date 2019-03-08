# RK3288 Source Code（For Face Recognition）

## 1 Prepare rk3288 Environment（Connect dev box and workstation in the same network）

### 1-1 get modified termux apk (Built from [here](https://github.com/SharpAI/mobile_app_server/tree/android_porting/AndroidPorting/Launcher))

#### 1-1-1 From Baidu (sharpai-norootfs-lambda_key.apk)
> Link: https://pan.baidu.com/s/1ic3jEItCNG8mgJQPlHBYhg Password: mq9p
#### 1-1-2 termux Compile
> Use Android studio to build https://github.com/SharpAI/mobile_app_server/tree/android_porting/AndroidPorting/Launcher

### 1-2 安装termux apk
#### 1-2-1 u盘安装
>u盘插入盒子后，手动安装

#### 1-2-2 adb安装
>本地计算机需要有adb环境
```
adb install sharpai-norootfs-lambda_key.apk
```
如下adb安装截图：




### 1-3 termux下安装 openssh

termux下安装ssh
```
$ pkg install openssh
```
启动ssh
```
$ sshd
```

PC上通过ssh连接盒子（盒子ip）
```
$ ssh -p 8022 xxx.xxx.xxx.xxx

```


#### c.更termux新源(当离线安装 termux 时，版本比较旧，建议更新,否则安装环境依赖graphicsmagick 可能报错)
```
$ rm -rf /data/data/com.termux/files/usr/var/lib/apt/*
$ apt-get update
```


### 1-2 安装源码运行环境
先下载下面这2个文件

>usr_dev_root_armv7_1126_2018.tgz
链接: https://pan.baidu.com/s/18GwmAj04ylqg1AYS5T5BQA 密码:0w8a
arch_dev_root_1203_2018_final.tgz
链接: https://pan.baidu.com/s/1FdaTiqjuLKEr7ZvKw2JF4g 密码:hvlz

rk3288盒子上(如下是盒子主动从电脑上通过ssh拉取，也可以电脑主动上传)：
```
$ cd /data/data/com.termux/files/
$ scp lambda@电脑的ip:/data/usr_dev_root_armv7_1126_2018.tgz .
$ tar -zxvmf usr_dev_root_armv7_1126_2018.tgz
$ rm -f usr_dev_root_armv7_1126_2018.tgz
$ cd /data/data/com.termux/files/home
$ scp lambda@电脑的ip:/data/arch_dev_root_1203_2018_final.tgz .
$ tar -zxvmf arch_dev_root_1203_2018_final.tgz
$ rm -f arch_dev_root_1203_2018_final.tgz
```
也可以通过adb桥接的方式上传usr_dev_root_armv7_1126_2018.tgz,arch_dev_root_1203_2018_final.tgz 到盒子
> 参见https://developer.android.com/studio/command-line/adb?hl=en-us

## 2 准备源码及运行环境
```
$ cd /data/data/com.termux/files/home
$ git clone https://github.com/SharpAI/sharpai

切换人形分支（需要的时候执行）
$ cd /data/data/com.termux/files/home/sharpai
$ git checkout origin/human_master_rk3399_linux -b human_master_rk3399_linux  

```
如果要安装人形模型
下载这个文件model-rk3288-termux.tgz(人脸模型model-armv7a.tgz)
> 人形模型下载链接: https://pan.baidu.com/s/1ic3jEItCNG8mgJQPlHBYhg 提取码: mq9p

上传、解压、移除
```
$ cd /data/data/com.termux/files/home/sharpai
$ tar -zxvmf model-rk3288-termux.tgz
$ rm -f model-rk3288-termux.tgz
```



安装必要的环境依赖
```
$ pip2 uninstall scipy
$ apt-get install python2-scipy

$ apt-get install graphicsmagick

$ cd /data/data/com.termux/files/home/sharpai/src/flower/
$ pip2 install -r requirements.txt

$ cd /data/data/com.termux/files/home/sharpai/src/detector/
$ npm install
```


## 3 开始运行
```
$ cd /data/data/com.termux/files/home/sharpai
$ ./start_service_arm32.sh
```

> 修改报错（如果运行报错，修改文件编码），
下面这几个文件的开头添加：
```
# -*-coding:UTF-8 -*-
```
文件：
>/data/data/com.termux/files/usr/lib/python2.7/site-packages/scipy-1.2.0-py2.7-linux-armv8l.egg/scipy/stats/_continuous_distns.py
/data/data/com.termux/files/usr/lib/python2.7/site-packages/scipy-1.2.0-py2.7-linux-armv8l.egg/scipy/stats/_stats_mstats_common.py
