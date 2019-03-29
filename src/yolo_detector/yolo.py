import numpy as np
import tvm
import time, os
import convert
import cv2
import json

from scipy import misc
from darknet import __darknetffi__
from tvm.contrib import graph_runtime
from cffi import FFI


def get_data(net, img_path, LIB):
    start = time.time()
    orig_image = LIB.load_image_color(img_path.encode('utf-8'), 0, 0)
    img_w = orig_image.w
    img_h = orig_image.h
    img = LIB.letterbox_image(orig_image, net.w, net.h)
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


class Yolo():
    def __init__(self):
        ctx = tvm.cl(0)
        ffi = FFI()

        DATA_RUNTIME_FOLDER = os.getenv('DATA_RUNTIME_FOLDER', '/data/runtime')

        self.darknet_lib = __darknetffi__.dlopen(DATA_RUNTIME_FOLDER + '/model/yolo/libdarknet.so')
        self.net = self.darknet_lib.load_network(DATA_RUNTIME_FOLDER + "/model/yolo/yolo.cfg", ffi.NULL, 0)

        lib = tvm.module.load(DATA_RUNTIME_FOLDER + '/model/yolo/yolo.tar')
        graph = open(DATA_RUNTIME_FOLDER + "/model/yolo/yolo").read()
        params = bytearray(open(DATA_RUNTIME_FOLDER + "/model/yolo/yolo.params", "rb").read())
        self.mod = graph_runtime.create(graph, lib, ctx)
        self.mod.load_params(params)

    def crop_persons(self, filename):
        im_w, im_h, data = get_data(self.net, filename, self.darknet_lib)
        print(data.shape)
        self.mod.set_input('data', tvm.nd.array(data.astype('float32')))
        self.mod.run()
        tvm_out = self.mod.get_output(0).asnumpy().flatten()
        print(tvm_out.shape)
        result = convert.calc_result(im_w, im_h, tvm_out)

        result_lines = result.splitlines()

        img = cv2.imread(filename)

        print(result_lines)
        result = []
        i = 0

        for line in result_lines:
            _, item, prob, xmin, ymin, xmax, ymax = line.split(' ')
            if item == 'person':
                print("Person", xmin, ymin, xmax, ymax, im_w, im_h)
                xmin = int(xmin)
                xmax = int(xmax)
                ymin = int(ymin)
                ymax = int(ymax)

                crop_human = img[ymin:ymax, xmin:xmax]
                aligned = cv2.resize(crop_human, (128, 384))

                width  = 128 #xmax - xmin
                height = 384 #ymax - ymin
                blury_value = int(cv2.Laplacian(aligned, cv2.CV_64F).var())

                crop_filename = filename.rsplit('.', 1)[0] + '_' + str(i) + '.' + 'png'

                result.append({
                    "filename": crop_filename,
                    "width": width,
                    "height": height,
                    "blury": blury_value})

                cv2.imwrite(crop_filename, aligned)
                i += 1

        return result

    def detect(self, image_path, trackerid, ts, cameraid, face_filter):
        cropped = []
        detected = False

        result = self.crop_persons(image_path)

        people_cnt = len(result)

        for item in result:
            print(item)
            detected = True
            cropped.append({"path": item['filename'], "style": 'front', "blury": item['blury'], "ts": ts,
                            "trackerid": trackerid, "totalPeople": people_cnt, "cameraId": cameraid,
                            "width": item['width'], "height": item['height']})

        return json.dumps(
            {'detected': detected, "ts": ts, "totalPeople": people_cnt, "cropped": cropped, 'totalmtcnn': people_cnt})


if __name__ == "__main__":
    yolo = Yolo()
    yolo.crop_persons("test1.png")
    yolo.crop_persons("test2.png")
    yolo.crop_persons("test3.png")
