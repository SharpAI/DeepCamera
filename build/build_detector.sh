#!/usr/bin/env bash

cd ../src/detector
npm install
npm run webpack
mv main.bin.js ../../build/runtime/
cp -rf node_modules ../../build/runtime/

cd -
cp scripts/start_detector.sh ./runtime/
echo "cd runtime; ./start_detector.sh to start the detector"
