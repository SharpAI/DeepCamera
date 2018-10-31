# -*- coding: UTF-8 -*-
import os
import cv2
import numpy as np
import urllib
import matplotlib
matplotlib.use('Agg')  # 无前端显示的情况下，执行脚本画图表并写入image文件中
import matplotlib.pyplot as plt
import matplotlib.animation as animation


def url_to_image(url):
    # download the image, convert it to a NumPy array, and then read
    # it into OpenCV format
    resp = urllib.urlopen(url)
    image = np.asarray(bytearray(resp.read()), dtype="uint8")
    image = cv2.imdecode(image, cv2.IMREAD_COLOR)

    # return the image
    return image


def load_all_images(dir):
    imgs = []
    for file_name in os.listdir(dir):
        if os.path.splitext(file_name)[-1] == '.JPG':
            pass
        # Remember that I had to flip the iPhone image, also the image was in BGR colorspace so I had to convert to RGB
        # img = cv2.cvtColor(cv2.imread(os.path.join(dir, file_name)), cv2.COLOR_BGR2RGB)[::-1, ::-1, :]
        img = cv2.cvtColor(cv2.imread(os.path.join(dir, file_name)), cv2.COLOR_BGR2RGB)
        imgs.append(img)

    return imgs


def build_gif(imgs, save_path, show_gif=True, save_gif=True, title=''):
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.set_axis_off()

    ims = map(lambda x: (ax.imshow(x), ax.set_title(title)), imgs)

    im_ani = animation.ArtistAnimation(fig, ims, interval=800, repeat_delay=0, blit=False)

    if save_gif:
        im_ani.save(save_path, writer='imagemagick')

    if show_gif:
        plt.show()

    return


if __name__ == '__main__':
    dir = ''
    imgs = load_all_images(dir)
    gif_path = 'animation.gif'
    build_gif(imgs=imgs, save_path=gif_path)