# Run On Android(AArch64)

## Get Launcher_Termux source code
```
git clone https://github.com/SharpAI/Launcher_Termux
```

## Config authorized_keys for ssh
Open Launcher_Termux, add your id_rsa.pub in authorized_keys

![add authorized keys](../screenshots/add_authorized_keys.png)

## Launch Launcher_Termux in Android Studio

## Install openssh in Launcher_Termux

```
pkg install openssh
sshd
```

## Remote access to Launcher_Termux through ssh

```
ssh -p 8022 a@Android_IP
```

