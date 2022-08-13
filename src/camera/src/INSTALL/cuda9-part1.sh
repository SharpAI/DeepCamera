sudo add-apt-repository ppa:graphics-drivers/ppa -y
sudo apt update -y
sudo apt install g++ freeglut3-dev build-essential libx11-dev libxmu-dev libxi-dev libglu1-mesa libglu1-mesa-dev -y
sudo apt install gcc-6 -y
sudo apt install g++-6 -y
wget https://cdn.shinobi.video/installers/cuda9-part2-after-reboot.sh -O cuda9-part2-after-reboot.sh
sudo chmod +x ./cuda9-part2-after-reboot.sh
wget https://developer.nvidia.com/compute/cuda/9.0/Prod/local_installers/cuda_9.0.176_384.81_linux-run -O cuda_9.run
sudo chmod +x cuda_9.run
sudo echo "blacklist amd76x_edac" >> /etc/modprobe.d/blacklist.conf
sudo echo "blacklist vga16fb" >> /etc/modprobe.d/blacklist.conf
sudo echo "blacklist nouveau" >> /etc/modprobe.d/blacklist.conf
sudo echo "blacklist rivafb" >> /etc/modprobe.d/blacklist.conf
sudo echo "blacklist nvidiafb" >> /etc/modprobe.d/blacklist.conf
sudo echo "blacklist rivatv" >> /etc/modprobe.d/blacklist.conf
sudo update-initramfs -u
echo "Now you need to reboot and run the next part."
echo "Do after the reboot inside this directory : ./cuda9-part2-after-reboot.sh"