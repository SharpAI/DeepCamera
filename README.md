# SharpAI On Android

## Download Termux Modified Version

```
git clone https://github.com/solderzzc/hotShare -b android_porting
```

## Add authorized key

AndroidPorting/Launcher/app/src/main/assets/authorized_keys

## Build and run it

## Setup

```
pkg install openssh
sshd
```

## Then Remote access it for easy

```
ssh -p 8022 a@192.168.x.x
```

## Install Base Root File System
```
cd /data/data/com.termux/files
wget https://github.com/solderzzc/model_release/releases/download/v1.0/usr_10312018.tgz
tar -xvf usr_10312018.tgz
```

## Restart TERMUX

## Run Sharp AI Code

```
git clone https://github.com/solderzzc/sharpai
cd sharpai
./setup.sh
./start_service.sh
```


