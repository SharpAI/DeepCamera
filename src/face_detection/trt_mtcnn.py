import time
import cv2
from mtcnn import TrtMtcnn

def get_result(boxes, landmarks):
    result = []
    for bb, ll in zip(boxes, landmarks):
        bbox =  [int(bb[0]), int(bb[1]), int(bb[2]), int(bb[3])]
        landmark = []
        for j in range(5):
            landmark.append([int(ll[j]), int(ll[j+5])])
        result.append({
            'score': 0.9999865,
            'bbox': bbox,
            'landmark': landmark
        })
    json_result = { 'result': result}
    return json_result

def main():
    mtcnn = TrtMtcnn()

    fps = 0.0
    tic = time.time()

    #img = cv2.imread('1_1920x1080.jpg')
    img = cv2.imread('1_854x480.jpg')
    while True:
        dets, landmarks = mtcnn.detect(img, minsize=50)
        result = get_result(dets, landmarks)
        # print(result)

        print('{} face(s) found, fps {}'.format(len(dets), fps))

        toc = time.time()
        curr_fps = 1.0 / (toc - tic)
        # calculate an exponentially decaying average of fps number
        fps = curr_fps if fps == 0.0 else (fps*0.95 + curr_fps*0.05)
        tic = toc

if __name__ == '__main__':
    main()
