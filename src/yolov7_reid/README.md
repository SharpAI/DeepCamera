# Yolov7 REID

Use AI to help kids get rid of misusing their laptops.


```
pip3 install sharpai-hub
sharpai-cli screen_monitor start
```

### Access streaming screen: http://localhost:8000
### Access labelstudio: http://localhost:8080

# Model is downloaded from [yolov5_fastreid_deepsort_tensorrt](https://github.com/linghu8812/yolov5_fastreid_deepsort_tensorrt)
# Train your own model with [fast-reid](https://github.com/JDAI-CV/fast-reid)

```
https://github.com/JDAI-CV/fast-reid
cd fast-reid
wget https://github.com/JDAI-CV/fast-reid/releases/download/v0.1.1/market_mgn_R50-ibn.pth
python3 tools/deploy/onnx_export.py --config-file configs/Market1501/mgn_R50-ibn.yml --name mgn_R50-ibn --output outputs/onnx_model --batch-size 1 --opts MODEL.WEIGHTS market_mgn_R50-ibn.pth
```