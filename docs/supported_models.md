# Supported AI Models

## Overview
DeepCamera supports various AI models for different detection and recognition tasks. This document provides a comprehensive list of supported models and their capabilities.

## Object Detection Models

### YOLOv5
- **Purpose**: General object detection
- **Supported Objects**: Person, car, bicycle, motorcycle, airplane, bus, train, truck, boat, traffic light, fire hydrant, etc.
- **Supported Architectures**: 
  - YOLOv5n (Nano)
  - YOLOv5s (Small)
  - YOLOv5m (Medium)
  - YOLOv5l (Large)
- **Performance**: Varies by model size and hardware
- **Supported Platforms**: x86_64, ARM64, ARMv7

### Face Detection
- **Model**: RetinaFace
- **Features**:
  - Face detection
  - Facial landmarks
  - Face alignment
- **Supported Platforms**: All platforms

## Recognition Models

### Face Recognition
- **Model**: ArcFace
- **Features**:
  - Face embedding generation
  - Face comparison
  - Face verification
- **Performance**: 99.5%+ accuracy on LFW benchmark
- **Supported Platforms**: All platforms

### Person Re-identification
- **Model**: OSNet
- **Features**:
  - Person feature extraction
  - Person matching across cameras
- **Supported Platforms**: x86_64, ARM64

## Special Purpose Models

### Fall Detection
- **Model**: Custom pose estimation
- **Features**:
  - Human pose detection
  - Fall event detection
- **Supported Platforms**: x86_64, ARM64

### Parking Detection
- **Model**: YOLOv5 custom trained
- **Features**:
  - Parking space occupancy detection
  - Vehicle type classification
- **Supported Platforms**: All platforms

### Intrusion Detection
- **Model**: Combined YOLOv5 + ReID
- **Features**:
  - Person detection
  - Movement tracking
  - Zone violation detection
- **Supported Platforms**: All platforms

## Hardware Acceleration Support

### NVIDIA GPU
- CUDA acceleration
- Supported for all models
- Requires CUDA 10.2+

### Intel CPU
- OpenVINO acceleration
- Supported for YOLOv5 and Face Detection
- Requires Intel processors

### Edge TPU
- Coral USB Accelerator support
- Limited model support
- Optimized for edge deployment

## Model Performance Comparison

### YOLOv5 Variants
| Model | Size | Speed (ms) | mAP@.5 | Platform Support |
|-------|------|------------|--------|------------------|
| YOLOv5n | 7.5MB | 6.3 | 45.7 | All |
| YOLOv5s | 14.1MB | 6.4 | 56.8 | All |
| YOLOv5m | 40.2MB | 8.2 | 64.1 | x86_64, ARM64 |
| YOLOv5l | 89.0MB | 10.1 | 67.3 | x86_64 |

### Face Recognition Models
| Model | Size | Speed (ms) | Accuracy | Platform Support |
|-------|------|------------|----------|------------------|
| ArcFace-r18 | 91MB | 7.3 | 99.60% | All |
| ArcFace-r34 | 130MB | 9.5 | 99.75% | x86_64, ARM64 |
| ArcFace-r50 | 166MB | 12.8 | 99.83% | x86_64 |

## Future Model Support
We are actively working on adding support for:
- YOLOv8
- CLIP for zero-shot detection
- More specialized detection models
- Improved edge device optimization

## Model Configuration
For information on how to configure and optimize these models for your specific use case, please refer to our [Configuration Guide](configuration_guide.md). 