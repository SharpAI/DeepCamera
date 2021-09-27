apt-get install -y libopenblas-dev

rm mxnet_cu102-1.6.0-py2.py3-none-linux_aarch64.whl && \
    cd /root && \
    wget https://gist.githubusercontent.com/dusty-nv/ce51796085178e1f38e3c6a1663a93a1/raw/bdb08d33760fc94ffbca20ed843c638228f8bb45/pytorch-1.4-diff-jetpack-4.4.patch  && \
    git clone --recursive --branch v1.4.0 http://github.com/pytorch/pytorch && \
    cd pytorch && \
    patch -p1 < ../pytorch-1.4-diff-jetpack-4.4.patch && \
    export USE_NCCL=0 && \
    export USE_TENSORRT=1 && \
    export USE_DISTRIBUTED=0 && \
    export USE_QNNPACK=0 && \
    export USE_CUDNN=0 && \
    export USE_PYTORCH_QNNPACK=0 && \
    export TORCH_CUDA_ARCH_LIST="5.3" && \
    export PYTORCH_BUILD_VERSION=1.4.0 && \
    export PYTORCH_BUILD_NUMBER=1 && \
    pip install -r requirements.txt && \
    pip install scikit-build --user && \
    pip install ninja --user && \
    python setup.py bdist_wheel