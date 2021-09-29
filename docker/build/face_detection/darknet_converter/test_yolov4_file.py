from yolov4_tiny import YoloModel, get_output
import cv2

model = YoloModel()


frame = cv2.imread('./210719_gma_cocogauff_hpMain_16x9_992.jpg')
boxes, confs, clss = model.trt_yolo.detect(frame, 0.7)
objs = get_output(boxes, confs, clss, 10)
print(objs)

img = model.vis.draw_bboxes(frame, boxes, confs, clss)
cv2.imwrite('test.jpg',img)
cv2.imshow('show', img)