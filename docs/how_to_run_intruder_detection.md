# Start DeepCamera
### 1. Start DeepCamera
```
sharpai-cli deepcamera start
```
### 2. Land-on Home-Assistant with URL: http://localhost:8123
### 3. Add your Camera through Home-Assistant camera integration
### 4. Added SharpAI configuration to configuration.yaml
```
stream:
  ll_hls: true
  part_duration: 0.75
  segment_duration: 6

image_processing:
  - platform: sharpai
    source:
      - entity_id: camera.<camera_entity_id>
    scan_interval: 1
```
### 5. Access detection result on [SharpAI website](http://dp.sharpai.org:3000)
### 6. Integration with Home-Assistant
### 7. [Implementation detail](docs/DeepCamera_introduction.md)
