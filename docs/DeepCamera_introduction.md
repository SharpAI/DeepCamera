# DeepCamera
- DeepCamera is a face recongnition NVR leverages [MTCNN](https://arxiv.org/abs/1604.02878) for face detection and [InsightFace's ArcFace](https://arxiv.org/abs/1801.07698) for face recognition, it leverages SVM from SKLearn as classifier and a private implemetation from Frank Zuo to fine-tune accuracy. To handle unbalanced dataset distribution which is most likely seen when you start to labelling unknown faces, we deployed upsampling policy to your own labelled face dataset. All the inference code as well as AutoML training code are running on your own device. 
- The DeepCamera commerical version which had been deployed to a large-scale AI smart city construction project has strong backend design to support large scale edge device cluster with redis. The commerical version provides private cloud deployment for security requirement.
- Learned from the open source community, it was a painful procedure to deploy a private cloud solution on your own device, we provide free cloud host for evaluation and non-commericial use with limited storage quota, so you can easily use following command line to setup DeepCamera on your own device in 5-minutes:

```
sharpai-cli deepcamera start
```
