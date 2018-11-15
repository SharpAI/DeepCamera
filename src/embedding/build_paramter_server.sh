#!/bin/bash

pyinstaller --name=param -y --hiddenimport email \
     --hiddenimport email.message \
     --hiddenimport email.mime.message \
     --hiddenimport email.mime.image \
     --hiddenimport email.mime.text \
     --hiddenimport email.mime.audio \
     --hiddenimport email.mime.base \
     --hiddenimport email.mime.multipart \
     --hiddenimport email.mime.nonmultipart \
     parameter_server.py --clean


echo "run with LD_LIBRARY_PATH=$LD_LIBRARY_PATH:./dist/param/ ./dist/param/param"
