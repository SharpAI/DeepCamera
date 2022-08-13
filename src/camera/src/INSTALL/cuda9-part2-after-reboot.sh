sudo service lightdm stop
sudo init 3
sudo ./cuda_9.run -- override
sudo ln -s /usr/bin/gcc-6 /usr/local/cuda/bin/gcc
sudo ln -s /usr/bin/g++-6 /usr/local/cuda/bin/g++
nvidia-smi