# -*- coding: UTF-8 -*-
import sys, glob, os
from retraining_tf import maybe_download_and_extract, create_inception_graph, resize, tf, \
    create_image_lists, cache_bottlenecks

from urllib import urlopen


filetypes = ['*.jpg', '*.jpeg']
summaries_dir = "/tmp/output_labels.txt"
BASE_FOLDER = os.path.join(os.getenv('RUNTIME_BASEDIR',os.path.abspath(os.path.dirname(__file__))), 'dataset')
BOTTLENECKS_FOLDER = os.path.join(os.getenv('RUNTIME_BASEDIR',os.path.abspath(os.path.dirname(__file__))), 'bottlenecks')

def download_img(img_url, group_id, face_id, i):
    u = urlopen(img_url)
    foldername = '{}{}'.format(group_id, face_id)
    folder_path = os.path.join(BASE_FOLDER, foldername)
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    filename = foldername + str(i) + '.jpg'
    local_path = os.path.join(folder_path, filename)

    if not os.path.isfile(local_path):
        with open(local_path, 'wb') as f:
            f.write(u.read())

    return os.path.join(foldername, filename)

def save_bottlenecks(image_dir=BASE_FOLDER, bottleneck_dir=BOTTLENECKS_FOLDER,
                     testing_percentage=10, validation_percentage=10,
                     resizeimages=False):
    if resizeimages:
        for filetype in filetypes:
            for single_jpg in glob.glob(filetype):
                print(single_jpg)
                resize(single_jpg)  # todo 图片路径相关变量（image_dir）可能要变化
        print("Done")

    # Setup the directory we'll write summaries to for TensorBoard
    if tf.gfile.Exists(summaries_dir):
        tf.gfile.DeleteRecursively(summaries_dir)
    tf.gfile.MakeDirs(summaries_dir)

    # Set up the pre-trained graph.
    maybe_download_and_extract()
    graph, bottleneck_tensor, jpeg_data_tensor, resized_image_tensor = (
        create_inception_graph())

    # Look at the folder structure, and create lists of all the images.
    image_lists = create_image_lists(image_dir, testing_percentage,
                                     validation_percentage)
    class_count = len(image_lists.keys())
    if class_count == 0:
        print('No valid folders of images found at ' + image_dir)
    if class_count == 1:
        print('Only one valid folder of images found at ' + image_dir +
              ' - multiple classes are needed for classification.')
    # See if the command-line flags mean we're applying any distortions.
    # do_distort_images = should_distort_images(
    #     flip_left_right, random_crop, random_scale,
    #     random_brightness)
    sess = tf.Session()

    # if do_distort_images:
    #     # We will be applying distortions, so setup the operations we'll need.
    #     distorted_jpeg_data_tensor, distorted_image_tensor = add_input_distortions(
    #         flip_left_right, random_crop, random_scale,
    #         random_brightness)
    # We'll make sure we've calculated the 'bottleneck' image summaries and
    # cached them on disk.
    cache_bottlenecks(sess, image_lists, image_dir, bottleneck_dir,
                      jpeg_data_tensor, bottleneck_tensor)

    return image_lists

if __name__ == '__main__':
    # 直接执行就是测试，需要本地目录有image_dir文件，格式为
    # ├── Data
    # │   ├── stuff1
    # │       ├── 1.jpg
    # │       ├── 2.jpg
    # │   ├── stuff2
    image_dir = "Data"
    bottleneck_dir = "bottlenecks"
    save_bottlenecks(image_dir, bottleneck_dir)
