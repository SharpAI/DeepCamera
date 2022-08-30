#!/bin/bash
docker buildx build --platform linux/amd64,linux/arm64/v8,linux/arm/v7,linux/arm/v6,linux/386 -t shareai/home-assiistant:2022.8 --push . 
