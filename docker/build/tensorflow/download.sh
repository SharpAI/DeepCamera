#!/bin/bash
if [ ! -f tensorflow-1.8.0-cp27-none-linux_armv7l.whl ]; then
   echo "need download tensorflow whl"
   wget https://github.com/lhelontra/tensorflow-on-arm/releases/download/v1.8.0/tensorflow-1.8.0-cp27-none-linux_armv7l.whl
else
   echo "tensorflow-1.8.0-cp27-none-linux_armv7l.whl already exists."
fi
