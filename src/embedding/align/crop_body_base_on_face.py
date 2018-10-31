# coding=utf-8

import numpy as np
from scipy import misc
from PIL import Image
import math

def resize_contain(image, size):
    """
    Resize image according to size.
    image:      a Pillow image instance
    size:       a list of two integers [width, height]
    """
    img_format = image.format
    img = image.copy()
    #img.thumbnail((size[0], size[1]), Image.LANCZOS)
    img.thumbnail((size[0], size[1]))
    background = Image.new('RGBA', (size[0], size[1]), (255, 255, 255, 0))
    img_position = (
        int(math.ceil((size[0] - img.size[0]) / 2)),
        int(math.ceil((size[1] - img.size[1]) / 2))
    )
    background.paste(img, img_position)
    background.format = img_format
    return background

def save_body_by_face_position(bb,origin_img,file_path):
    img_size = np.asarray(origin_img.shape)[0:2]
    img_width = img_size[1]
    img_height = img_size[0]

    face_width = bb[2] - bb[0]
    face_height = bb[3] - bb[1]

    bbox = np.zeros(4, dtype=np.int32)
    bbox[0] = np.maximum(bb[0] - face_width,0)               # 身体左外侧
    bbox[1] = np.maximum(bb[1] - face_height*0.2,0)          # 头顶向上找脸的0.2倍
    bbox[2] = np.minimum(bb[2] + face_width,img_width-1)     # 身体右外侧
    bbox[3] = np.minimum(bb[3] + face_height*7,img_height-1) # 成年人一般脸高比八倍左右，实际采集大部分高度会是到底的

    new_width = bbox[2] - bbox[0]
    new_height = bbox[3] - bbox[1]

    img = misc.toimage(origin_img)

    #img = img.crop((bbox[0],bbox[1],new_width,new_height))
    cropped = origin_img[bbox[1]:bbox[3], bbox[0]:bbox[2], :]
    img = misc.toimage(cropped)
    img = resize_contain(img, [128, 128])

    img.save(file_path,img.format)

    scale_height = new_height / face_height
    scale_width = new_width / face_width

def save_body_by_face_position_jpg(bb,origin_img,file_path):
    img_size = np.asarray(origin_img.shape)[0:2]
    img_width = img_size[1]
    img_height = img_size[0]

    face_width = bb[2] - bb[0]
    face_height = bb[3] - bb[1]

    bbox = np.zeros(4, dtype=np.int32)
    bbox[0] = np.maximum(bb[0] - face_width,0)               # 身体左外侧
    bbox[1] = np.maximum(bb[1] - face_height*0.2,0)          # 头顶向上找脸的0.2倍
    bbox[2] = np.minimum(bb[2] + face_width,img_width-1)     # 身体右外侧
    bbox[3] = np.minimum(bb[3] + face_height*7,img_height-1) # 成年人一般脸高比八倍左右，实际采集大部分高度会是到底的

    new_width = bbox[2] - bbox[0]
    new_height = bbox[3] - bbox[1]

    scale_height = new_height / face_height
    scale_width = new_width / face_width

    if scale_height < 3.0:
        return None,scale_width,scale_height

    img = misc.toimage(origin_img)

    #img = img.crop((bbox[0],bbox[1],new_width,new_height))
    cropped = origin_img[bbox[1]:bbox[3], bbox[0]:bbox[2], :]
    img = misc.toimage(cropped)
    img = resize_contain(img, [128, 128])

    img = img.convert("RGB")
    img.save(file_path,img.format)

    return True,scale_width,scale_height
