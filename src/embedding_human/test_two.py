# coding=utf-8
import FaceProcessing
import numpy as np
import sys
import argparse

def compare(emb1, emb2):
    dist = np.sqrt(np.sum(np.square(np.subtract(emb1, emb2))))

    d = emb1 - emb2
    print(
        "  + Squared l2 distance between representations: {:0.3f}".format(np.dot(d, d)))

    print('  %1.4f ' % (dist))
    return dist
def parse_arguments(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument('image1', type=str, 
        help='Image file 1')
    parser.add_argument('image2', type=str, 
        help='Image file 2')
    return parser.parse_args(argv)

if __name__ == '__main__':
    args = parse_arguments(sys.argv[1:])
    sess, graph = FaceProcessing.InitialFaceProcessor()
    embedding1 = FaceProcessing.FaceProcessingOne(args.image1,sess, graph)[0]
    embedding2 = FaceProcessing.FaceProcessingOne(args.image2,sess, graph)[0]
    compare(embedding2,embedding1)
