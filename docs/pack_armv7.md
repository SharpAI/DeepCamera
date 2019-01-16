---
# 2018-12-25 编译生成rk3288上sharpai的apk方法
---

### 1 准备编译和打包环境
cr12/s这个盒子刷开发用的img，与正常img唯一的区别是启动之后/data有5.8G
```
链接: https://pan.baidu.com/s/1ulWfSFngzE2AXGp9DymKFw 提取码: 6mbd
```

开机之后安装我们代码编译的termux.
启动termux安装openssh, 然后启动sshd, 这样pc上可以通过下面命令连接盒子。
```
ssh -p 8022 a@192.xx.xxx.xxx
```

准备termux的编译环境
```
$ wget http://192.168.254.16:8080/usr_dev_root_armv7_1126_2018.tgz
$ wget http://192.168.254.16:8080/arch_dev_root_1203_2018_final.tgz

$ tar -zxmf usr_dev_root_armv7_1126_2018.tgz
$ cd ..
$ mv home/usr_dev_root_armv7_1126_2018.tgz .
$ ls
home                              usr                               usr_dev_root_armv7_1126_2018.tgz
$ tar -zxmf usr_dev_root_armv7_1126_2018.tgz
$ rm usr_dev_root_armv7_1126_2018.tgz

$ cd
$ tar -zxvmf arch_dev_root_1203_2018_final.tgz


$ cd 
$ git clone https://github.com/solderzzc/sharpai
```

### 2 在盒子上生成sharpai-app.tgz
```
$ cd sharpai/
$ ./setup_arm32.sh

$ cd
$ cd sharpai/build/
$ ./build_arm.sh  ./

-rw------- 1 u0_a54 u0_a54 415M Dec 26 14:38 sharpai-app.tgz
```

### 3 生成apk
把上面生成的sharpai-app.tgz拷贝到PC上，放到这个目录hotShare/AndroidPorting/Launcher/app/src/main/assets/
同时这个目录还要有sharpai-base.tgz
编译好之后的apk文件就可以安装到rk3288上
编译apk时候使用的key https://github.com/solderzzc/hotShare/blob/sharpai/hotShareMobile/keystore
