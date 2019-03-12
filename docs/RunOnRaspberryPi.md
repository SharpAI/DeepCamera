## Install 64 bit Ubuntu for Raspberry Pi 3B+
https://wiki.ubuntu.com/ARM/RaspberryPi

Download: [ubuntu-18.04.2-preinstalled-server-arm64+raspi3.img.xz](http://cdimage.ubuntu.com/ubuntu/releases/bionic/release/ubuntu-18.04.2-preinstalled-server-arm64+raspi3.img.xz)

[Burn Image](https://www.raspberrypi.org/documentation/installation/installing-images/README.md)

## Install Docker
https://www.raspberrypi.org/blog/docker-comes-to-raspberry-pi/
```
curl -sSL https://get.docker.com | sh
```

## Setup Permission to use docker
https://docs.docker.com/install/linux/linux-postinstall/

## Install docker-compose
```
sudo apt install docker-compose
```

## Enable swap to get rid of freezed

[Reference](https://raspberrypi.stackexchange.com/questions/70/how-to-set-up-swap-space)

```
apt-get install dphys-swapfile
vi /etc/dphys-swapfile
```
Set swap to 2048M
```
CONF_SWAPSIZE=2048
```

Restart service
```
/etc/init.d/dphys-swapfile restart
```
## Get Deep Camera Source Code

```
git clone https://github.com/SharpAI/DeepCamera -b pi
cd DeepCamera/docker
./run-deepeye-raspberrypi.sh start
```

Then follow the instruction on the [main readme](https://github.com/SharpAI/DeepCamera#how-to-run-deepcamera-from-source-code)


