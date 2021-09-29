CC=g++
LD=ld
CXXFLAGS=-Wall -std=c++11 -g -O

NVCC=nvcc

cpu_arch=$(shell uname -m)
ifeq ($(cpu_arch), aarch64)  # Jetson
  chip_id=$(shell cat /sys/module/tegra_fuse/parameters/tegra_chip_id)
  ifeq ($(chip_id), 33)       # Nano and TX1
    compute=53
  else ifeq ($(chip_id), 24)  # TX2
    compute=62
  else ifeq ($(chip_id), 25)  # Xavier NX
    compute=72
  else
    $(error Cannot determine cuda compute automatically, so please modify Makefile manually)
  endif
else ifeq ($(cpu_arch), x86_64)  # x86_64 PC
  #$(warning "compute=75" is for GeForce RTX-2080 Ti.  Please make sure CUDA compute is set correctly for your system in the Makefile.)
  compute=75
else
  $(error Unkown CPU architecture: neither "aarch" nor "x86_64")
endif

#NVCCFLAGS=-m64 -gencode arch=compute_$(compute),code=sm_$(compute) \
#               -gencode arch=compute_$(compute),code=compute_$(compute)

# Let nvcc determine cuda compute automatically
NVCCFLAGS=

# These are the directories where I installed TensorRT on my x86_64 PC.
TENSORRT_INCS=-I"/usr/local/TensorRT-7.1.3.4/include"
TENSORRT_LIBS=-L"/usr/local/TensorRT-7.1.3.4/lib"

# INCS and LIBS
INCS=-I"/usr/local/cuda/include" $(TENSORRT_INCS) -I"/usr/local/include" -I"plugin"
LIBS=-L"/usr/local/cuda/lib64" $(TENSORRT_LIBS) -L"/usr/local/lib" -Wl,--start-group -lnvinfer -lnvparsers -lnvinfer_plugin -lcudnn -lcublas -lcudart_static -lnvToolsExt -lcudart -lrt -ldl -lpthread -Wl,--end-group

.PHONY: all clean

all: libyolo_layer.so

clean:
	rm -f *.so *.o

libyolo_layer.so: yolo_layer.o
	$(CC) -shared -o $@ $< $(LIBS)

yolo_layer.o: yolo_layer.cu yolo_layer.h
	$(NVCC) -ccbin $(CC) $(INCS) $(NVCCFLAGS) -Xcompiler -fPIC -c -o $@ $<
