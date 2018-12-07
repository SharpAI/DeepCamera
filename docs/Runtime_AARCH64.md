# SharpAI On Android AARCH64

## 1. Install Launcher/RTSP HW DECODER on Android

### On PC
- Download RTSP_HW_DECODER 
链接:https://pan.baidu.com/s/1RtZ4U-35JEtWVPe5e-7njQ  密码:xyqq
- Download Launcher
链接:https://pan.baidu.com/s/1R27adfdhU8PG8W0Sp3-5XA  密码:dpd7
- Install adb on PC

- adb connect ip

- adb install apk

## 2. Download usr.tgz and runtime.tgz

### 百度云盘 (TODO: ROOTFS还需要做精简)
#### usr_10312018.tgz
链接: https://pan.baidu.com/s/1hG6z2BdXCy82xtjXu3mrZg 提取码: 54cp

#### runtime.tgz
链接:https://pan.baidu.com/s/1O28aDrMTWbG6vapDlmBiEA  密码:0ugm

## 3. Install Base Root File System

### ON PC
```
adb push usr_10312018.tgz /data/data/com.termux/files/
adb push runtime_aarch64_1128_2018.tgz /data/data/com.termux/files/home/
```
### On Android Termux:
```
cd 
cd ..
tar -zxf usr_10312018.tgz

cd home
tar -zxf runtime_aarch64_1128_2018.tgz

cd runtime
./start_aarch64.sh
```

## 4. Get Serial No

```
cat ~/.ro_serialno
```

## 5. Generate QR Code from serialno(from step 4)

For example: `https://www.qr-code-generator.com`, `text mode`

## 6. Scan QR Code and add device in ’来了吗‘

## 7. Configure RTSP URL in RTSP HW Decoder

Click 'start play' should working now.
