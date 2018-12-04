#!/usr/bin/env bash
cd dist/stress_gpu/
LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$PREFIX/lib64 ./stress_gpu
