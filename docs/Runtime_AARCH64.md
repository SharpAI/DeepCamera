# SharpAI On Android AARCH64

## 1. Install Launcher/RTSP HW DECODER on Android

### On PC
- Download RTSP_HW_DECODER 
链接:https://pan.baidu.com/s/1Ghp_So4ADVedkmivFh7rqQ  密码:19k5
- Download Launcher
链接:https://pan.baidu.com/s/1R27adfdhU8PG8W0Sp3-5XA  密码:dpd7
- Install adb on PC

- adb connect ip

- adb install apk

### On Android Launcher (Termux Console)
```
pkg install openssh
sshd
```

## 2. Add id_rsa.pub to 
```
~/.ssh/authorized_keys 
```

## 3. Then Remote access it for easy

```
ssh -p 8022 a@192.168.x.x
```

## 4. Install Base Root File System

### ON PC

百度云盘

链接: https://pan.baidu.com/s/1hG6z2BdXCy82xtjXu3mrZg 提取码: 54cp
```
scp -P 8022 usr_10312018.tgz a@ip:/data/data/com.termux/files
```
### On Android
```
cd /data/data/com.termux/files
tar -xvf usr_10312018.tgz 
```

## 5. Install Runtime


### On PC
链接:https://pan.baidu.com/s/1q82sDODnlH5wOohNJkQRGw  密码:d7xw

```
scp -P 8022 runtime_1127_src_2018.tgz a@ip:/data/data/com.termux/files/home
```

### On Android
```
cd ~/
tar -zxvf runtime_1127_src_2018.tgz
cd runtime
./start_aarch64.sh
```

## 6. Get Serial No

```
cat ~/.ro_serialno
```

## 7. Generate QR Code from serialno(from step 6)

For example: `https://www.qr-code-generator.com`, `text mode`

## 8. Scan QR Code and add device in ’来了吗‘

## 9. Configure RTSP URL in RTSP HW Decoder


Click 'start play' should working now.
