#!/usr/bin/env bash
runtime=$(realpath $1)"/runtime"
cd ../src/detector
npm install
npm run webpack
mv main.bin.js $runtime/
cp -rf node_modules $runtime/
cp -rf config $runtime/

cd -
cp scripts/start_detector.sh $runtime/
echo "cd $runtime; ./start_detector.sh to start the detector"
