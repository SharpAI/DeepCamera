#!/bin/bash
docker buildx build --push --platform linux/amd64,linux/arm64 --tag shareai/label-studio:1.5.0 .

