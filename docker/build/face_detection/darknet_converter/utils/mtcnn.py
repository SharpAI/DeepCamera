"""mtcnn_trt.py
"""

import numpy as np
import cv2
import pytrt


PIXEL_MEAN = 127.5
PIXEL_SCALE = 0.0078125


def convert_to_1x1(boxes):
    """Convert detection boxes to 1:1 sizes

    # Arguments
        boxes: numpy array, shape (n,5), dtype=float32

    # Returns
        boxes_1x1
    """
    boxes_1x1 = boxes.copy()
    hh = boxes[:, 3] - boxes[:, 1] + 1.
    ww = boxes[:, 2] - boxes[:, 0] + 1.
    mm = np.maximum(hh, ww)
    boxes_1x1[:, 0] = boxes[:, 0] + ww * 0.5 - mm * 0.5
    boxes_1x1[:, 1] = boxes[:, 1] + hh * 0.5 - mm * 0.5
    boxes_1x1[:, 2] = boxes_1x1[:, 0] + mm - 1.
    boxes_1x1[:, 3] = boxes_1x1[:, 1] + mm - 1.
    boxes_1x1[:, 0:4] = np.fix(boxes_1x1[:, 0:4])
    return boxes_1x1


def crop_img_with_padding(img, box, padding=0):
    """Crop a box from image, with out-of-boundary pixels padded

    # Arguments
        img: img as a numpy array, shape (H, W, 3)
        box: numpy array, shape (5,) or (4,)
        padding: integer value for padded pixels

    # Returns
        cropped_im: cropped image as a numpy array, shape (H, W, 3)
    """
    img_h, img_w, _ = img.shape
    if box.shape[0] == 5:
        cx1, cy1, cx2, cy2, _ = box.astype(int)
    elif box.shape[0] == 4:
        cx1, cy1, cx2, cy2 = box.astype(int)
    else:
        raise ValueError
    cw = cx2 - cx1 + 1
    ch = cy2 - cy1 + 1
    cropped_im = np.zeros((ch, cw, 3), dtype=np.uint8) + padding
    ex1 = max(0, -cx1)  # ex/ey's are the destination coordinates
    ey1 = max(0, -cy1)
    ex2 = min(cw, img_w - cx1)
    ey2 = min(ch, img_h - cy1)
    fx1 = max(cx1, 0)  # fx/fy's are the source coordinates
    fy1 = max(cy1, 0)
    fx2 = min(cx2+1, img_w)
    fy2 = min(cy2+1, img_h)
    cropped_im[ey1:ey2, ex1:ex2, :] = img[fy1:fy2, fx1:fx2, :]
    return cropped_im


def nms(boxes, threshold, type='Union'):
    """Non-Maximum Supression

    # Arguments
        boxes: numpy array [:, 0:5] of [x1, y1, x2, y2, score]'s
        threshold: confidence/score threshold, e.g. 0.5
        type: 'Union' or 'Min'

    # Returns
        A list of indices indicating the result of NMS
    """
    if boxes.shape[0] == 0:
        return []
    xx1, yy1, xx2, yy2 = boxes[:, 0], boxes[:, 1], boxes[:, 2], boxes[:, 3]
    areas = np.multiply(xx2-xx1+1, yy2-yy1+1)
    sorted_idx = boxes[:, 4].argsort()

    pick = []
    while len(sorted_idx) > 0:
        # In each loop, pick the last box (highest score) and remove
        # all other boxes with IoU over threshold
        tx1 = np.maximum(xx1[sorted_idx[-1]], xx1[sorted_idx[0:-1]])
        ty1 = np.maximum(yy1[sorted_idx[-1]], yy1[sorted_idx[0:-1]])
        tx2 = np.minimum(xx2[sorted_idx[-1]], xx2[sorted_idx[0:-1]])
        ty2 = np.minimum(yy2[sorted_idx[-1]], yy2[sorted_idx[0:-1]])
        tw = np.maximum(0.0, tx2 - tx1 + 1)
        th = np.maximum(0.0, ty2 - ty1 + 1)
        inter = tw * th
        if type == 'Min':
            iou = inter / \
                  np.minimum(areas[sorted_idx[-1]], areas[sorted_idx[0:-1]])
        else:
            iou = inter / \
                  (areas[sorted_idx[-1]] + areas[sorted_idx[0:-1]] - inter)
        pick.append(sorted_idx[-1])
        sorted_idx = sorted_idx[np.where(iou <= threshold)[0]]
    return pick


def generate_pnet_bboxes(conf, reg, scale, t):
    """
    # Arguments
        conf: softmax score (face or not) of each grid
        reg: regression values of x1, y1, x2, y2 coordinates.
             The values are normalized to grid width (12) and
             height (12).
        scale: scale-down factor with respect to original image
        t: confidence threshold

    # Returns
        A numpy array of bounding box coordinates and the
        cooresponding scores: [[x1, y1, x2, y2, score], ...]

    # Notes
        Top left corner coordinates of each grid is (x*2, y*2),
        or (x*2/scale, y*2/scale) in the original image.
        Bottom right corner coordinates is (x*2+12-1, y*2+12-1),
        or ((x*2+12-1)/scale, (y*2+12-1)/scale) in the original
        image.
    """
    conf = conf.T  # swap H and W dimensions
    dx1 = reg[0, :, :].T
    dy1 = reg[1, :, :].T
    dx2 = reg[2, :, :].T
    dy2 = reg[3, :, :].T
    (x, y) = np.where(conf >= t)
    if len(x) == 0:
        return np.zeros((0, 5), np.float32)

    score = np.array(conf[x, y]).reshape(-1, 1)          # Nx1
    reg = np.array([dx1[x, y], dy1[x, y],
                    dx2[x, y], dy2[x, y]]).T * 12.       # Nx4
    topleft = np.array([x, y], dtype=np.float32).T * 2.  # Nx2
    bottomright = topleft + np.array([11., 11.], dtype=np.float32)  # Nx2
    boxes = (np.concatenate((topleft, bottomright), axis=1) + reg) / scale
    boxes = np.concatenate((boxes, score), axis=1)       # Nx5
    # filter bboxes which are too small
    #boxes = boxes[boxes[:, 2]-boxes[:, 0] >= 12., :]
    #boxes = boxes[boxes[:, 3]-boxes[:, 1] >= 12., :]
    return boxes


def generate_rnet_bboxes(conf, reg, pboxes, t):
    """
    # Arguments
        conf: softmax score (face or not) of each box
        reg: regression values of x1, y1, x2, y2 coordinates.
             The values are normalized to box width and height.
        pboxes: input boxes to RNet
        t: confidence threshold

    # Returns
        boxes: a numpy array of box coordinates and cooresponding
               scores: [[x1, y1, x2, y2, score], ...]
    """
    boxes = pboxes.copy()  # make a copy
    assert boxes.shape[0] == conf.shape[0]
    boxes[:, 4] = conf  # update 'score' of all boxes
    boxes = boxes[conf >= t, :]
    reg = reg[conf >= t, :]
    ww = (boxes[:, 2]-boxes[:, 0]+1).reshape(-1, 1)  # x2 - x1 + 1
    hh = (boxes[:, 3]-boxes[:, 1]+1).reshape(-1, 1)  # y2 - y1 + 1
    boxes[:, 0:4] += np.concatenate((ww, hh, ww, hh), axis=1) * reg
    return boxes


def generate_onet_outputs(conf, reg_boxes, reg_marks, rboxes, t):
    """
    # Arguments
        conf: softmax score (face or not) of each box
        reg_boxes: regression values of x1, y1, x2, y2
                   The values are normalized to box width and height.
        reg_marks: regression values of the 5 facial landmark points
        rboxes: input boxes to ONet (already converted to 2x1)
        t: confidence threshold

    # Returns
        boxes: a numpy array of box coordinates and cooresponding
               scores: [[x1, y1, x2, y2,... , score], ...]
        landmarks: a numpy array of facial landmark coordinates:
                   [[x1, x2, ..., x5, y1, y2, ..., y5], ...]
    """
    boxes = rboxes.copy()  # make a copy
    assert boxes.shape[0] == conf.shape[0]
    boxes[:, 4] = conf
    boxes = boxes[conf >= t, :]
    reg_boxes = reg_boxes[conf >= t, :]
    reg_marks = reg_marks[conf >= t, :]
    xx = boxes[:, 0].reshape(-1, 1)
    yy = boxes[:, 1].reshape(-1, 1)
    ww = (boxes[:, 2]-boxes[:, 0]).reshape(-1, 1)
    hh = (boxes[:, 3]-boxes[:, 1]).reshape(-1, 1)
    marks = np.concatenate((xx, xx, xx, xx, xx, yy, yy, yy, yy, yy), axis=1)
    marks += np.concatenate((ww, ww, ww, ww, ww, hh, hh, hh, hh, hh), axis=1) * reg_marks
    ww = ww + 1
    hh = hh + 1
    boxes[:, 0:4] += np.concatenate((ww, hh, ww, hh), axis=1) * reg_boxes
    return boxes, marks


def clip_dets(dets, img_w, img_h):
    """Round and clip detection (x1, y1, ...) values.

    Note we exclude the last value of 'dets' in computation since
    it is 'conf'.
    """
    dets[:, 0:-1] = np.fix(dets[:, 0:-1])
    evens = np.arange(0, dets.shape[1]-1, 2)
    odds  = np.arange(1, dets.shape[1]-1, 2)
    dets[:, evens] = np.clip(dets[:, evens], 0., float(img_w-1))
    dets[:, odds]  = np.clip(dets[:, odds], 0., float(img_h-1))
    return dets


class TrtPNet(object):
    """TrtPNet

    Refer to mtcnn/det1_relu.prototxt for calculation of input/output
    dimmensions of TrtPNet, as well as input H offsets (for all scales).
    The output H offsets are merely input offsets divided by stride (2).
    """
    input_h_offsets  = (0, 216, 370, 478, 556, 610, 648, 676, 696)
    output_h_offsets = (0, 108, 185, 239, 278, 305, 324, 338, 348)
    max_n_scales = 9

    def __init__(self, engine):
        """__init__

        # Arguments
            engine: path to the TensorRT engine file
        """
        self.trtnet = pytrt.PyTrtMtcnn(engine,
                                       (3, 710, 384),
                                       (2, 350, 187),
                                       (4, 350, 187))
        self.trtnet.set_batchsize(1)

    def detect(self, img, minsize=40, factor=0.709, threshold=0.7):
        """Detect faces using PNet

        # Arguments
            img: input image as a RGB numpy array
            threshold: confidence threshold

        # Returns
            A numpy array of bounding box coordinates and the
            cooresponding scores: [[x1, y1, x2, y2, score], ...]
        """
        if minsize < 40:
            raise ValueError("TrtPNet is currently designed with "
                             "'minsize' >= 40")
        if factor > 0.709:
            raise ValueError("TrtPNet is currently designed with "
                             "'factor' <= 0.709")
        m = 12.0 / minsize
        img_h, img_w, _ = img.shape
        minl = min(img_h, img_w) * m

        # create scale pyramid
        scales = []
        while minl >= 12:
            scales.append(m)
            m *= factor
            minl *= factor
        if len(scales) > self.max_n_scales:  # probably won't happen...
            raise ValueError('Too many scales, try increasing minsize '
                             'or decreasing factor.')

        total_boxes = np.zeros((0, 5), dtype=np.float32)
        img = (img.astype(np.float32) - PIXEL_MEAN) * PIXEL_SCALE

        # stack all scales of the input image vertically into 1 big
        # image, and only do inferencing once
        im_data = np.zeros((1, 3, 710, 384), dtype=np.float32)
        for i, scale in enumerate(scales):
            h_offset = self.input_h_offsets[i]
            h = int(img_h * scale)
            w = int(img_w * scale)
            im_data[0, :, h_offset:(h_offset+h), :w] = \
                cv2.resize(img, (w, h)).transpose((2, 0, 1))

        out = self.trtnet.forward(im_data)

        # extract outputs of each scale from the big output blob
        for i, scale in enumerate(scales):
            h_offset = self.output_h_offsets[i]
            h = (int(img_h * scale) - 12) // 2 + 1
            w = (int(img_w * scale) - 12) // 2 + 1
            pp = out['prob1'][0, 1, h_offset:(h_offset+h), :w]
            cc = out['boxes'][0, :, h_offset:(h_offset+h), :w]
            boxes = generate_pnet_bboxes(pp, cc, scale, threshold)
            if boxes.shape[0] > 0:
                pick = nms(boxes, 0.5, 'Union')
                if len(pick) > 0:
                    boxes = boxes[pick, :]
            if boxes.shape[0] > 0:
                total_boxes = np.concatenate((total_boxes, boxes), axis=0)

        if total_boxes.shape[0] == 0:
            return total_boxes
        pick = nms(total_boxes, 0.7, 'Union')
        dets = clip_dets(total_boxes[pick, :], img_w, img_h)
        return dets

    def destroy(self):
        self.trtnet.destroy()
        self.trtnet = None


class TrtRNet(object):
    """TrtRNet

    # Arguments
        engine: path to the TensorRT engine (det2) file
    """

    def __init__(self, engine):
        self.trtnet = pytrt.PyTrtMtcnn(engine,
                                       (3, 24, 24),
                                       (2, 1, 1),
                                       (4, 1, 1))

    def detect(self, img, boxes, max_batch=256, threshold=0.6):
        """Detect faces using RNet

        # Arguments
            img: input image as a RGB numpy array
            boxes: detection results by PNet, a numpy array [:, 0:5]
                   of [x1, y1, x2, y2, score]'s
            max_batch: only process these many top boxes from PNet
            threshold: confidence threshold

        # Returns
            A numpy array of bounding box coordinates and the
            cooresponding scores: [[x1, y1, x2, y2, score], ...]
        """
        if max_batch > 256:
            raise ValueError('Bad max_batch: %d' % max_batch)
        boxes = boxes[:max_batch]  # assuming boxes are sorted by score
        if boxes.shape[0] == 0:
            return boxes
        img_h, img_w, _ = img.shape
        boxes = convert_to_1x1(boxes)
        crops = np.zeros((boxes.shape[0], 24, 24, 3), dtype=np.uint8)
        for i, det in enumerate(boxes):
            cropped_im = crop_img_with_padding(img, det)
            # NOTE: H and W dimensions need to be transposed for RNet!
            crops[i, ...] = cv2.transpose(cv2.resize(cropped_im, (24, 24)))
        crops = crops.transpose((0, 3, 1, 2))  # NHWC -> NCHW
        crops = (crops.astype(np.float32) - PIXEL_MEAN) * PIXEL_SCALE

        self.trtnet.set_batchsize(crops.shape[0])
        out = self.trtnet.forward(crops)

        pp = out['prob1'][:, 1, 0, 0]
        cc = out['boxes'][:, :, 0, 0]
        boxes = generate_rnet_bboxes(pp, cc, boxes, threshold)
        if boxes.shape[0] == 0:
            return boxes
        pick = nms(boxes, 0.7, 'Union')
        dets = clip_dets(boxes[pick, :], img_w, img_h)
        return dets

    def destroy(self):
        self.trtnet.destroy()
        self.trtnet = None


class TrtONet(object):
    """TrtONet

    # Arguments
        engine: path to the TensorRT engine (det3) file
    """

    def __init__(self, engine):
        self.trtnet = pytrt.PyTrtMtcnn(engine,
                                       (3, 48, 48),
                                       (2, 1, 1),
                                       (4, 1, 1),
                                       (10, 1, 1))

    def detect(self, img, boxes, max_batch=64, threshold=0.7):
        """Detect faces using ONet

        # Arguments
            img: input image as a RGB numpy array
            boxes: detection results by RNet, a numpy array [:, 0:5]
                   of [x1, y1, x2, y2, score]'s
            max_batch: only process these many top boxes from RNet
            threshold: confidence threshold

        # Returns
            dets: boxes and conf scores
            landmarks
        """
        if max_batch > 64:
            raise ValueError('Bad max_batch: %d' % max_batch)
        if boxes.shape[0] == 0:
            return (np.zeros((0, 5), dtype=np.float32),
                    np.zeros((0, 10), dtype=np.float32))
        boxes = boxes[:max_batch]  # assuming boxes are sorted by score
        img_h, img_w, _ = img.shape
        boxes = convert_to_1x1(boxes)
        crops = np.zeros((boxes.shape[0], 48, 48, 3), dtype=np.uint8)
        for i, det in enumerate(boxes):
            cropped_im = crop_img_with_padding(img, det)
            # NOTE: H and W dimensions need to be transposed for RNet!
            crops[i, ...] = cv2.transpose(cv2.resize(cropped_im, (48, 48)))
        crops = crops.transpose((0, 3, 1, 2))  # NHWC -> NCHW
        crops = (crops.astype(np.float32) - PIXEL_MEAN) * PIXEL_SCALE

        self.trtnet.set_batchsize(crops.shape[0])
        out = self.trtnet.forward(crops)

        pp = out['prob1'][:, 1, 0, 0]
        cc = out['boxes'][:, :, 0, 0]
        mm = out['landmarks'][:, :, 0, 0]
        boxes, landmarks = generate_onet_outputs(pp, cc, mm, boxes, threshold)
        pick = nms(boxes, 0.7, 'Min')
        return (clip_dets(boxes[pick, :], img_w, img_h),
                np.fix(landmarks[pick, :]))

    def destroy(self):
        self.trtnet.destroy()
        self.trtnet = None


class TrtMtcnn(object):
    """TrtMtcnn"""

    def __init__(self):
        self.pnet = TrtPNet('mtcnn/det1.engine')
        self.rnet = TrtRNet('mtcnn/det2.engine')
        self.onet = TrtONet('mtcnn/det3.engine')

    def __del__(self):
        self.onet.destroy()
        self.rnet.destroy()
        self.pnet.destroy()

    def _detect_1280x720(self, img, minsize):
        """_detec_1280x720()

        Assuming 'img' has been resized to less than 1280x720.
        """
        # MTCNN model was trained with 'MATLAB' image so its channel
        # order is RGB instead of BGR.
        img = img[:, :, ::-1]  # BGR -> RGB
        dets = self.pnet.detect(img, minsize=minsize)
        dets = self.rnet.detect(img, dets)
        dets, landmarks = self.onet.detect(img, dets)
        return dets, landmarks

    def detect(self, img, minsize=40):
        """detect()

        This function handles rescaling of the input image if it's
        larger than 1280x720.
        """
        if img is None:
            raise ValueError
        img_h, img_w, _ = img.shape
        scale = min(720. / img_h, 1280. / img_w)
        if scale < 1.0:
            new_h = int(np.ceil(img_h * scale))
            new_w = int(np.ceil(img_w * scale))
            img = cv2.resize(img, (new_w, new_h))
            minsize = max(int(np.ceil(minsize * scale)), 40)
        dets, landmarks = self._detect_1280x720(img, minsize)
        if scale < 1.0:
            dets[:, :-1] = np.fix(dets[:, :-1] / scale)
            landmarks = np.fix(landmarks / scale)
        return dets, landmarks
