## Setup Termux Linux Development Environment
直接安装耗时较长，可以下载已经制作好的开发环境

### Download 

### Install
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

## Build Termux Runtime

## Clean up Termux Linux Development Environment

## Setup Termux Linux and Arch Linux Environment

## Build Arch Linux Runtime

## Clean Up
