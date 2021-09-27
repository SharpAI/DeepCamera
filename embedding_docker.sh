#!/bin/bash
sudo docker run --gpus all -it --rm --runtime=nvidia -e DISPLAY=$DISPLAY --network=host -v $(pwd):/root/DeepCamera shareai/embedding:nano_latest /bin/bash
