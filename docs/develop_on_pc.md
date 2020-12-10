
## On X86 Linux
1. Install Docker
```
sudo curl -sSL https://get.docker.com | sh
```
2. Install Docker-compose
```
sudo curl -L "https://github.com/docker/compose/releases/download/1.27.4/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```
3. Get source code
```
git clone https://github.com/SharpAI/DeepCamera
```
4. Start container
```
cd DeepCamera/
./run-on-linux.sh start
```
## On OSX
1. Install Docker
[Install Docker Desktop on Mac(Offical)](https://docs.docker.com/docker-for-mac/install/)
2. Get source code
```
git clone https://github.com/SharpAI/DeepCamera
```
3. Start container
```
cd DeepCamera/
./run-on-mac.sh start
```
