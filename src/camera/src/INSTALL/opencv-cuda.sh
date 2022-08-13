# OpenCV CUDA

wget -O opencv.zip https://github.com/opencv/opencv/archive/3.4.0.zip
wget -O opencv_contrib.zip https://github.com/opencv/opencv_contrib/archive/3.4.0.zip
sudo apt-get install unzip -y

sudo unzip opencv.zip -d tempOpenCV
sudo unzip opencv_contrib.zip -d tempOpenCVContrib

sudo mv tempOpenCV/opencv-3.4.0 opencv
sudo mv tempOpenCVContrib/opencv_contrib-3.4.0 opencv_contrib
sudo rm -rf tempOpenCV
sudo rm -rf tempOpenCVContrib

sudo apt install build-essential cmake git pkg-config unzip ffmpeg qtbase5-dev python-dev python3-dev python-numpy python3-numpy libhdf5-dev libgtk-3-dev libdc1394-22 libdc1394-22-dev libjpeg-dev libtiff5-dev libtesseract-dev -y

sudo add-apt-repository "deb http://security.ubuntu.com/ubuntu zesty-security main"
sudo add-apt-repository "deb http://security.ubuntu.com/ubuntu xenial-security main"
sudo apt update
sudo apt install libjasper1 libjasper-dev libavcodec-dev libavformat-dev libswscale-dev libxine2-dev libgstreamer-plugins-base1.0-0 libgstreamer-plugins-base1.0-dev libpng16-16 libpng-dev libv4l-dev libtbb-dev libfaac-dev libmp3lame-dev libopencore-amrnb-dev libopencore-amrwb-dev libtheora-dev libvorbis-dev libxvidcore-dev v4l-utils -y

cd opencv
mkdir release
cd release

cmake -D CMAKE_INSTALL_PREFIX=/usr/local -D WITH_NVCUVID=ON -D FORCE_VTK=ON -D BUILD_DOCS=ON -D WITH_XINE=ON -D WITH_CUDA=ON -D WITH_OPENGL=ON -D WITH_TBB=ON -D BUILD_EXAMPLES=ON -D WITH_OPENCL=ON -D CMAKE_BUILD_TYPE=RELEASE -D CUDA_NVCC_FLAGS="-D_FORCE_INLINES --expt-relaxed-constexpr" -D WITH_GDAL=ON -D OPENCV_EXTRA_MODULES_PATH=../../opencv_contrib/modules/ -D ENABLE_FAST_MATH=1 -D CUDA_FAST_MATH=1 -D WITH_CUBLAS=1 ..

make -j4
sudo make install