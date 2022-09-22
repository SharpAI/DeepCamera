#!/bin/bash
docker buildx build --push --platform linux/amd64,linux/arm64 \
--tag sharpai/redis:3.2.11 .
