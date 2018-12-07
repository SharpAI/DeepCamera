## Setup USB Storage
```
sudo mkfs.ext4 /dev/sdX1
sudo tune2fs -o acl /dev/sdX1
sudo mount /dev/sdX1 /mnt
sudo chown <username>: /mnt
chmod 777 /mnt
setfacl -m d:u::rwx,d:g::rwx,d:o::rwx /mnt
sudo umount /mnt
```

## On Android
```
chown u0_a78:u0_a78 u/mnt/usb_storage/USB_DISK2/disk0 
```

## Setup Termux Linux Development Environment
#### usr_dev_root_1128_2018.tgz
#### 包含了除SVM之外的编译运行依赖，这是开发用的
链接:https://pan.baidu.com/s/1MjlCUiiUVf0z_ILoZ7y44w  密码:3rh7

空间不够了，这样节省一些：
```
pkg uninstall gcc-6 gcc-7 gcc-8
```
## Build Termux Runtime
Use sharpai/build/build_arm.sh to Build

## Clean up Termux Linux Development Environment
## Setup Termux Linux and Arch Linux Environment

直接安装耗时较长，可以下载已经制作好的开发环境

### （方法一）Download From Baidu Pan
arch_dev_root_1203_2018_final.tgz
链接:https://pan.baidu.com/s/1_GnaOZ9urmhjX0RcFlKq7w  密码:eio5
```
scp -p 8022 arch_dev_root_1203_2018_final.tgz /data/data/com.termux/files/home
```

```
cd
tar -zxf arch_dev_root_1203_2018_final.tgz
pkg install proot
./arch/startarch
```
### （方法二）Install Through Network
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
## Build Arch Linux Runtime
```
cd sharpai/build
bash ./build_arm_arch.sh /mnt/internal_sd/
```
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

`./arch/startarch c "cd /data/data/com.termux/files/home/runtime_arch/bin && ./worker worker --loglevel INFO -E -n detect -c 2 -Q detect"`
