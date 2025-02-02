# Home Assistant Integration Guide

## Overview
DeepCamera can be seamlessly integrated with Home Assistant to provide advanced AI-powered camera features in your smart home setup. This guide will walk you through the complete integration process.

## Prerequisites
- Home Assistant installed and running
- DeepCamera installed and configured
- A compatible camera set up in your network

## Integration Steps

### 1. Install DeepCamera Component
First, ensure DeepCamera is properly installed and running on your system. You can verify this by checking if the DeepCamera service is active:

```bash
docker ps | grep deepcamera
```

### 2. Configure Home Assistant

#### 2.1 Add Required Configuration
Edit your Home Assistant `configuration.yaml` file and add the following configuration:

```yaml
# Enable streaming support
stream:
  ll_hls: true
  part_duration: 0.75
  segment_duration: 6

# Configure DeepCamera integration
image_processing:
  - platform: sharpai
    source:
      - entity_id: camera.<your_camera_entity_id>
    scan_interval: 6
```

#### 2.2 Configure Camera Entity
Make sure your camera is properly configured in Home Assistant. Add the following to your `configuration.yaml` if not already present:

```yaml
camera:
  - platform: generic
    name: My Camera
    still_image_url: http://<camera_ip>/snapshot
    stream_source: rtsp://<camera_ip>/stream
```

### 3. Set Up Notifications (Optional)
To receive notifications when DeepCamera detects events:

```yaml
automation:
  - alias: "DeepCamera Detection Notification"
    trigger:
      platform: event
      event_type: sharpai_detection
    action:
      - service: notify.notify
        data:
          title: "DeepCamera Detection"
          message: "{{ trigger.event.data.detection_type }} detected"
```

### 4. Restart and Verify
1. Save all configuration changes
2. Restart Home Assistant
3. Check the Home Assistant logs for any errors
4. Verify that the integration appears in your Home Assistant dashboard

## Advanced Configuration

### Custom Detection Settings
You can customize detection settings for different scenarios:

```yaml
image_processing:
  - platform: sharpai
    source:
      - entity_id: camera.front_door
    scan_interval: 6
    confidence: 80
    detection_types:
      - person
      - vehicle
      - animal
```

### Multiple Camera Setup
For multiple cameras:

```yaml
image_processing:
  - platform: sharpai
    source:
      - entity_id: camera.front_door
      - entity_id: camera.back_door
      - entity_id: camera.garage
    scan_interval: 6
```

## Troubleshooting

### Common Issues and Solutions

1. **Integration Not Appearing**
   - Verify DeepCamera service is running
   - Check Home Assistant logs for errors
   - Ensure camera entity is correctly configured

2. **No Detections**
   - Verify camera stream is accessible
   - Check scan_interval settings
   - Verify detection confidence settings

3. **Performance Issues**
   - Adjust scan_interval to balance performance
   - Check network bandwidth
   - Monitor system resources

## Additional Resources
- [DeepCamera Documentation](https://github.com/SharpAI/DeepCamera)
- [Home Assistant Documentation](https://www.home-assistant.io/integrations/)
- [Community Support Forum](https://community.home-assistant.io/) 