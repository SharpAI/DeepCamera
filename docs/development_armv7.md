# 准备工作
## 开发和产品所需要的资源文件

|系统|版本|文件名|下载地址|
|:-:|:-:|:-:|:-:|
|Termux|开发|usr_dev_root_armv7_1126_2018.tgz|链接: https://pan.baidu.com/s/18GwmAj04ylqg1AYS5T5BQA  密码:0w8a|
|Termux|产品|usr_runtime_root_1126_2018.tgz|链接: https://pan.baidu.com/s/1toQ7kfEMF4JkMVr0GuevPg  密码:nk1j|
|Arch|开发|arch_dev_root_1203_2018_final.tgz|链接: https://pan.baidu.com/s/1FdaTiqjuLKEr7ZvKw2JF4g  密码:hvlz|
|Arch|产品|arch_usr_runtime_1203_2018_final.tgz|链接: https://pan.baidu.com/s/13WwQzuwy9mljzAbhhEeEYA  密码:p1va|

## 3288的存储空间很小，外挂USB移动硬盘开发
`外挂移动硬盘无法编译nodejs detector，需要在外挂之前先把nodejs部分编译，然后保存起来`
#### On PC
```
sudo mkfs.ext4 /dev/sdX1
sudo tune2fs -o acl /dev/sdX1
sudo mount /dev/sdX1 /mnt
sudo chown <username>: /mnt
chmod 777 /mnt
setfacl -m d:u::rwx,d:g::rwx,d:o::rwx /mnt
sudo umount /mnt
```

#### On Android
```
chown u0_a78:u0_a78 u/mnt/usb_storage/USB_DISK2/disk0 
```

# 开发流程
## 设置 Termux Linux 开发环境
### PC端
```
scp -p 8022 <Termux_开发.tgz> a@ip:/data/data/com.termux/files/
```
### Android端
```
cd /data/data/com.termux/files
tar -zxvf <Termux_开发.tgz>
```
## 编译Termux中的运行程序
```
cd sharpai/
./setup_arm32.sh
cd build/
bash build_arm.sh ./
```
## 设置 Arch Linux 开发环境

#### 使用板子Flash资源
```
scp -p 8022 <arch_开发.tgz> /data/data/com.termux/files/home
```

```
tar -zxf <arch_开发.tgz>
pkg install proot
./arch/startarch
```
#### 使用外接移动硬盘
```
su
mount
umount /mnt/usb_storage/USB_DISK2/udisk2 <--在上一步检查出哪个是移动硬盘
mount -o rw -t ext4 /dev/block/vold/8:3 /data/data/com.termux/files/home 
exit
pkg install tsu
tsu
tar -zxf <arch_开发.tgz>
bash ./arch/startarch
```
## 编译 Arch Linux 中的运行程序
```
cd sharpai/build
bash ./build_arm_arch.sh /mnt/internal_sd/
```

# 制作运行系统

```
cd /data/data/com.termux/files
tar -zxvf <Termux_产品.tgz> 
cd /data/data/com.termux/files/home
tar --exclude=arch/etc/ca-certificates/extracted/cadir/* -zxvf <Termux_产品.tgz>
tar -xvf /mnt/internal_sd/runtime.tar
tar -xvf /mnt/internal_sd/runtime_arch.tar
pkg install proot
```


# 系统打包

|日期|描述|链接|
|:-:|:-:|:-:|
|1207-2018|Flower没跑 Monitor没跑 GM没装没有Gif|链接:https://pan.baidu.com/s/1FR30UEfFnPqc11UBNA9wbg  密码:3uzn|

# 分隔符，以下没有整理


## Clean Up

```
exit
bash ./setupTermuxArch.sh purge
```


## Prepare ARCH Linux rootfs

### （方法一）下载
链接:https://pan.baidu.com/s/1ZUbdVTAiChSdO0ZoFA2bUQ  密码:br1p

### （方法二）网络安装

## 运行


`./arch/startarch c "cd /data/data/com.termux/files/home/runtime_arch/bin && ./classifier "`

`./arch/startarch c "cd /data/data/com.termux/files/home/runtime_arch/bin && ./worker worker --loglevel INFO -E -n detect -c 1 -Q detect"`




## ARCH Linux 开发环境制作方法
```
pkg install wget
$PREFIX/bin/wget https://sdrausty.github.io/TermuxArch/setupTermuxArch.sh
bash setupTermuxArch.sh
rm -rf /lib/firmware/*
pacman -S python python-scikit-learn python-pip
pacman -Syu base-devel opencv opencv-samples
find /var -name *.xz -delete
pacman -S hdf5 gtk3 cmake vtk glew git
pacman -S python-matplotlib python-pillow  
pip install wheel
pip install scikit-image
pip install pyinstaller
```
