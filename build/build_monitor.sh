#!/usr/bin/env bash
runtime=$(realpath $1)"/runtime"
cd ../src/monitor
npm install
npm run webpack
mkdir -p $runtime/monitor
mv main.bin.js $runtime/monitor
cp -rf node_modules $runtime/monitor

cd -
cp scripts/start_monitor.sh $runtime/
echo "cd $runtime; ./start_monitor.sh to start the monitor"
