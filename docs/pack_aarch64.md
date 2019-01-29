arch64上打包sharpai，以及在7420上面验证，rk3399没有验证

## 1 7420编译环境准备
### 1-1 刷7420的系统，刷完后确保内核版本如下
```
在板子上执行
$ uname -a
Linux localhost 3.10.61-g7a23fb8-dirty #168 SMP PREEMPT Fri Nov 2 18:59:38 CST 2018 aarch64 Android
```
### 1-2 安装termux，PC通过ssh连接板子
### 1-3 替换lib
在板子上执行如下命令。其中 lambda@192.168.254.16是我自己的PC存放有相关文件
```
$ scp lambda@192.168.254.16:/data2/vendor.tgz .
$ su
# mount -o remount,rw /system
# tar -zxvmf /data/data/com.termux/files/home/vendor.tgz -C /system
# exit
```
!!千万注意是/system，不是/system/vender


### 1-4 准备termux文件系统以及sharpai源码
在板子上执行
```
$ cd /data/data/com.termux/files/
$ scp lambda@192.168.254.16:/data2/usr_aarch64_dev_1204_2018.tgz .
$ tar -zxvmf usr_aarch64_dev_1204_2018.tgz
$ rm usr_aarch64_dev_1204_2018.tgz
$ cd /data/data/com.termux/files/home

$ pkg install ncurses-utils

$ git clone https://github.com/solderzzc/sharpai
$ cd sharpai/
$ ./setup.sh
```

## 2 7420上编译打包
板子上执行
```
$ cd sharpai/build/
$ ./build_aarch64.sh ./
...
creating sharpai-app.tgz ...
-rw------- 1 u0_a53 u0_a53 323M Jan  7 08:41 sharpai-app-aarch64.tgz
```


## 3 生成7420上面安装的apk
把上面生成的sharpai-app-aarch64.tgz拷贝到PC上，放到这个目录hotShare/AndroidPorting/Launcher/app/src/main/assets/sharpai-app.tgz 同时这个目录还要有7420对应的sharpai-base.tgz 编译好之后的apk文件就可以安装到7420上

 编译apk时候使用的key https://github.com/solderzzc/hotShare/blob/sharpai/hotShareMobile/keystore
