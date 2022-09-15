

### Access home-assistant[http://localhost:8123](http://localhost:8123)

### Add camera to home-assistant

### Edit configuration file

```

docker exec -ti home-assistant /bin/bash

vi configuration.yaml
```

### Add sharpai image_processing integration:

```
stream:
  ll_hls: true
  part_duration: 0.75
  segment_duration: 6

image_processing:
  - platform: sharpai
    source:
      - entity_id: camera.<camera_entity_id>
    scan_interval: 6
```

### Reload Home-Assistant
