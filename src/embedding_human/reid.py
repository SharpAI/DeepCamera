import tvm
import numpy as np
import time, os
import sklearn.preprocessing
import base64

from StringIO import StringIO
from PIL import Image
from tvm.contrib import graph_runtime


def human_distance(enc1, enc2):
    return np.sqrt(np.sum(np.square(enc1 - enc2)))


def transform_image(image):
    image = np.array(image) - np.array([123., 117., 104.])
    image /= np.array([58.395, 57.12, 57.375])
    image = image.transpose((2, 0, 1))
    image = image[np.newaxis, :]
    return image


class ReId:
    def __init__(self):
        DATA_RUNTIME_FOLDER = os.getenv('DATA_RUNTIME_FOLDER', '/data/runtime/model')

        # tvm module for compiled functions.
        loaded_lib = tvm.module.load(DATA_RUNTIME_FOLDER + '/reid.tar')
        # json graph
        loaded_json = open(DATA_RUNTIME_FOLDER + "/reid").read()
        # parameters in binary
        loaded_params = bytearray(open(DATA_RUNTIME_FOLDER + "/reid.params", "rb").read())

        ctx = tvm.cl(0)
        self.mod = graph_runtime.create(loaded_json, loaded_lib, ctx)
        self.mod.load_params(loaded_params)

    def get_embeding(self, file_name):
        start = time.time()
        data = transform_image(Image.open(file_name).resize((128, 256)))

        self.mod.set_input('data', tvm.nd.array(data.astype('float32')))
        self.mod.run()

        embeding = self.mod.get_output(0).asnumpy()
        embeding = sklearn.preprocessing.normalize(embeding).flatten()
        done = time.time()
        return embeding

    def get_embeding_from_base64(self, base64_string):
        sbuf = StringIO()
        sbuf.write(base64.b64decode(base64_string))
        return self.get_embeding(sbuf)

    @staticmethod
    def get_distance(feature1, feature2):
        return human_distance(feature1, feature2)


if __name__ == "__main__":
    reid = ReId()

    feature1 = reid.get_embeding("0001_c1s1_001051_00.jpg")
    feature2 = reid.get_embeding("0001_c6s1_009676_02.jpg")
    feature3 = reid.get_embeding("0008_c1s1_000376_02.jpg")

    print("distance1-2", reid.get_distance(feature1, feature2))
    print("distance1-3", reid.get_distance(feature1, feature3))
    print("distance2-3", reid.get_distance(feature2, feature3))
