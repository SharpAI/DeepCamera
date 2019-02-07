import numpy as np
import tvm
import time
import convert
import cv2

from darknet import __darknetffi__
from tvm.contrib import graph_runtime


def get_data(img_path, LIB):
    start = time.time()
    orig_image = LIB.load_image_color(img_path.encode('utf-8'), 0, 0)
    img_w = orig_image.w
    img_h = orig_image.h
    img = LIB.letterbox_image(orig_image, 608, 608)
    LIB.free_image(orig_image)
    done = time.time()
    print('1: Image Load run {}'.format((done - start)))

    data = np.empty([img.c, img.h, img.w], 'float32')
    start = time.time()
    convert.float32_convert(data, img.data)
    done = time.time()
    print('2: data convert in C {}'.format((done - start)))

    LIB.free_image(img)
    return img_w, img_h, data


def compute_iou(box, boxes, box_area, boxes_area):
    """Calculates IoU of the given box with the array of the given boxes.
    box: 1D vector [y1, x1, y2, x2]
    boxes: [boxes_count, (y1, x1, y2, x2)]
    box_area: float. the area of 'box'
    boxes_area: array of length boxes_count.
    Note: the areas are passed in rather than calculated here for
    efficiency. Calculate once in the caller to avoid duplicate work.
    """
    # Calculate intersection areas
    y1 = np.maximum(box[0], boxes[:, 0])
    y2 = np.minimum(box[2], boxes[:, 2])
    x1 = np.maximum(box[1], boxes[:, 1])
    x2 = np.minimum(box[3], boxes[:, 3])
    intersection = np.maximum(x2 - x1, 0) * np.maximum(y2 - y1, 0)
    union = box_area + boxes_area[:] - intersection[:]
    iou = intersection * 1.0 / union
    return iou


def compute_overlaps(boxes1, boxes2):
    """Computes IoU overlaps between two sets of boxes.
    boxes1, boxes2: [N, (y1, x1, y2, x2)].
    For better performance, pass the largest set first and the smaller second.
    """
    # Areas of anchors and GT boxes
    area1 = (boxes1[:, 2] - boxes1[:, 0]) * (boxes1[:, 3] - boxes1[:, 1])
    area2 = (boxes2[:, 2] - boxes2[:, 0]) * (boxes2[:, 3] - boxes2[:, 1])

    # Compute overlaps to generate matrix [boxes1 count, boxes2 count]
    # Each cell contains the IoU value.
    overlaps = np.zeros((boxes1.shape[0], boxes2.shape[0]))
    for i in range(overlaps.shape[1]):
        box2 = boxes2[i]
        overlaps[:, i] = compute_iou(box2, boxes1, area2[i], area1)
    return overlaps


class Yolo():
    def __init__(self):
        ctx = tvm.cl(0)

        self.darknet_lib = __darknetffi__.dlopen('../../model/yolo/libdarknet.so')

        lib = tvm.module.load('../../model/yolo/yolov2.tar')
        graph = open("../../model/yolo/yolov2").read()
        params = bytearray(open("../../model/yolo/yolov2.params", "rb").read())
        self.mod = graph_runtime.create(graph, lib, ctx)
        self.mod.load_params(params)
        print("mod load params successfully")

        self.parked_car_boxes = None
        self.free_space_frames = 0
        self.frame_index = 0

    def get_car_boxes(self, filename):
        im_w, im_h, data = get_data(filename, self.darknet_lib)

        self.mod.set_input('data', tvm.nd.array(data.astype('float32')))

        print("run", data.shape)
        self.mod.run()
        print("get_output")
        tvm_out = self.mod.get_output(0).asnumpy().flatten()
        print("tvm_out", tvm_out.shape)
        result = convert.calc_result(im_w, im_h, tvm_out)

        result_lines = result.splitlines()

        # print(result_lines)

        car_boxes = []
        for line in result_lines:
            _, item, prob, xmin, ymin, xmax, ymax = line.split(' ')
            if item == 'car':
                # print("car", xmin, ymin, xmax, ymax, im_w, im_h)
                xmin = int(xmin)
                xmax = int(xmax)
                ymin = int(ymin)
                ymax = int(ymax)

                car_boxes.append((ymin, xmin, ymax, xmax))

        return np.array(car_boxes)

    def detect(self, image_path):

        img = cv2.imread(image_path)
        print("img.image_path", image_path)
        print("img.shape", img.shape)

        if self.parked_car_boxes is None:
            # This is the first frame of video - assume all the cars detected are in parking spaces.
            # Save the location of each car as a parking space box and go to the next frame of video.
            self.parked_car_boxes = self.get_car_boxes(image_path)
        else:
            # We already know where the parking spaces are. Check if any are currently unoccupied.

            # Get where cars are currently located in the frame
            car_boxes = self.get_car_boxes(image_path)

            print("self.parked_car_boxes", self.parked_car_boxes)
            print("car_boxes", car_boxes)

            # See how much those cars overlap with the known parking spaces
            overlaps = compute_overlaps(self.parked_car_boxes, car_boxes)

            print("overlaps", overlaps)
            # Assume no spaces are free until we find one that is free
            free_space = False

            # Loop through each known parking space box
            for parking_area, overlap_areas in zip(self.parked_car_boxes, overlaps):

                # For this parking space, find the max amount it was covered by any
                # car that was detected in our image (doesn't really matter which car)
                max_IoU_overlap = np.max(overlap_areas)
                max_IoU_overlap = float("%0.2f" % (max_IoU_overlap))

                print("max_IoU_overlap", max_IoU_overlap)
                # Get the top-left and bottom-right coordinates of the parking area
                y1, x1, y2, x2 = parking_area

                # Check if the parking space is occupied by seeing if any car overlaps
                # it by more than 0.15 using IoU
                if max_IoU_overlap < 0.15:
                    # Parking space not occupied! Draw a green box around it
                    cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 3)
                    # Flag that we have seen at least one open space
                    free_space = True
                else:
                    # Parking space is still occupied - draw a red box around it
                    cv2.rectangle(img, (x1, y1), (x2, y2), (0, 0, 255), 1)

                # Write the IoU measurement inside the box
                font = cv2.FONT_HERSHEY_DUPLEX

                cv2.putText(img, str(max_IoU_overlap), (x1 + 6, y2 - 6), font, 0.3, (255, 255, 255))

            cv2.imwrite("parking-"+str(self.frame_index)+".jpg", img)
            print("imwrite ", "parking-"+str(self.frame_index)+".jpg")
            # If at least one space was free, start counting frames
            # This is so we don't alert based on one frame of a spot being open.
            # This helps prevent the script triggered on one bad detection.
            if free_space:
                self.free_space_frames += 1
            else:
                # If no spots are free, reset the count
                self.free_space_frames = 0

            print("free_space_frames", self.free_space_frames)
            # If a space has been free for several frames, we are pretty sure it is really free!
            if self.free_space_frames > 10:
                print("SPACE AVAILABLE!")
                # Write SPACE AVAILABLE!! at the top of the screen
                font = cv2.FONT_HERSHEY_DUPLEX
                cv2.putText(img, "SPACE AVAILABLE!", (10, 150), font, 3.0, (0, 255, 0), 2, cv2.FILLED)
                cv2.imwrite("parking-avail.png", img)

        self.frame_index = self.frame_index + 1


if __name__ == "__main__":
    yolo = Yolo()
    yolo.detect("frame-1-0000.jpg")
    yolo.detect("frame-1-0000.jpg")


