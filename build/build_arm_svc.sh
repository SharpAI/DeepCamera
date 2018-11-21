#!/usr/bin/env bash

rm -rf build dist runtime
mkdir runtime
pyinstaller classifier_rest_single_thread_server.spec
mv dist/classifier runtime/bin
