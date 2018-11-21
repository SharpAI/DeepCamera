#!/usr/bin/env bash

rm -rf build dist runtime
mkdir runtime
pyinstaller classifier_server.spec
mv dist/classifier runtime/bin
