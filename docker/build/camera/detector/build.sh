#!/bin/bash

files=$(find . -maxdepth 1 -name "*.js")
for f in ${files}
do
    echo $f
    filename=$(basename ${f})
    ./uglifyjs-es-cmd --compress --mangle -c -o dist/release/${filename}  ${filename}
done

files=$(find ./libs/ -maxdepth 1 -name "*.js")
for f in ${files}
do
    echo $f
    filename=$(basename ${f})
    ./uglifyjs-es-cmd --compress --mangle -c -o dist/release/libs/${filename}  ./libs/${filename}
done
