# -*- coding: UTF-8 -*-
import os
from datetime import datetime
from tensorflow.python.platform import gfile
from tensorflow.python.framework import graph_util
from retraining_tf import add_final_training_ops, add_evaluation_step, get_random_distorted_bottlenecks, \
    get_random_cached_bottlenecks, create_inception_graph, tf

eval_step_interval = 10
final_tensor_name = "final_result"
summaries_dir = "/tmp/output_labels.txt"
how_many_training_steps = 500
train_batch_size = 100
validation_batch_size = 100
test_batch_size = -1
image_dir = os.path.join("Animal_Data")
print_misclassified_test_images = False
output_graph = "output_graph.pb"
output_labels = "output_labels.txt"

# Setup the directory we'll write summaries to for TensorBoard
if tf.gfile.Exists(summaries_dir):
    tf.gfile.DeleteRecursively(summaries_dir)
tf.gfile.MakeDirs(summaries_dir)

# Set up the pre-trained graph.
graph, bottleneck_tensor, jpeg_data_tensor, resized_image_tensor = (
    create_inception_graph())


def tf_train(image_lists, bottleneck_dir):
    sess = tf.Session()
    # Add the new layer that we'll be training.
    (train_step, cross_entropy, bottleneck_input, ground_truth_input,
     final_tensor) = add_final_training_ops(len(image_lists.keys()),
                                            final_tensor_name,
                                            bottleneck_tensor)

    # Create the operations we need to evaluate the accuracy of our new layer.
    evaluation_step, prediction = add_evaluation_step(
        final_tensor, ground_truth_input)

    # Merge all the summaries and write them out to /tmp/retrain_logs (by default)
    merged = tf.summary.merge_all()
    train_writer = tf.summary.FileWriter(summaries_dir + '/train',
                                         sess.graph)
    validation_writer = tf.summary.FileWriter(summaries_dir + '/validation')

    # Set up all our weights to their initial default values.
    init = tf.global_variables_initializer()
    sess.run(init)

    # Run the training for as many cycles as requested on the command line.
    for i in range(how_many_training_steps):
        # Get a batch of input bottleneck values, either calculated fresh every time
        # with distortions applied, or from the cache stored on disk.
        # if do_distort_images:
        #     train_bottlenecks, train_ground_truth = get_random_distorted_bottlenecks(
        #         sess, image_lists, train_batch_size, 'training',
        #         image_dir, distorted_jpeg_data_tensor,
        #         distorted_image_tensor, resized_image_tensor, bottleneck_tensor)
        # else:
        train_bottlenecks, train_ground_truth, _ = get_random_cached_bottlenecks(
            sess, image_lists, train_batch_size, 'training',
            bottleneck_dir, image_dir, jpeg_data_tensor,
            bottleneck_tensor)
        # Feed the bottlenecks and ground truth into the graph, and run a training
        # step. Capture training summaries for TensorBoard with the `merged` op.
        train_summary, _ = sess.run([merged, train_step],
                                    feed_dict={bottleneck_input: train_bottlenecks,
                                               ground_truth_input: train_ground_truth})
        train_writer.add_summary(train_summary, i)

        # Every so often, print out how well the graph is training.
        is_last_step = (i + 1 == how_many_training_steps)
        if (i % eval_step_interval) == 0 or is_last_step:
            train_accuracy, cross_entropy_value = sess.run(
                [evaluation_step, cross_entropy],
                feed_dict={bottleneck_input: train_bottlenecks,
                           ground_truth_input: train_ground_truth})
            print('%s: Step %d: Train accuracy = %.1f%%' % (datetime.now(), i,
                                                            train_accuracy * 100))
            print('%s: Step %d: Cross entropy = %f' % (datetime.now(), i,
                                                       cross_entropy_value))
            validation_bottlenecks, validation_ground_truth, _ = (
                get_random_cached_bottlenecks(
                    sess, image_lists, validation_batch_size, 'validation',
                    bottleneck_dir, image_dir, jpeg_data_tensor,
                    bottleneck_tensor))
            # Run a validation step and capture training summaries for TensorBoard
            # with the `merged` op.
            validation_summary, validation_accuracy = sess.run(
                [merged, evaluation_step],
                feed_dict={bottleneck_input: validation_bottlenecks,
                           ground_truth_input: validation_ground_truth})
            validation_writer.add_summary(validation_summary, i)
            print('%s: Step %d: Validation accuracy = %.1f%% (N=%d)' %
                  (datetime.now(), i, validation_accuracy * 100,
                   len(validation_bottlenecks)))

    # We've completed all our training, so run a final test evaluation on
    # some new images we haven't used before.
    test_bottlenecks, test_ground_truth, test_filenames = (
        get_random_cached_bottlenecks(sess, image_lists, test_batch_size,
                                      'testing', bottleneck_dir,
                                      image_dir, jpeg_data_tensor,
                                      bottleneck_tensor))
    test_accuracy, predictions = sess.run(
        [evaluation_step, prediction],
        feed_dict={bottleneck_input: test_bottlenecks,
                   ground_truth_input: test_ground_truth})
    print('Final test accuracy = %.1f%% (N=%d)' % (
        test_accuracy * 100, len(test_bottlenecks)))

    if print_misclassified_test_images:
        print('=== MISCLASSIFIED TEST IMAGES ===')
        for i, test_filename in enumerate(test_filenames):
            if predictions[i] != test_ground_truth[i].argmax():
                print('%70s  %s' % (test_filename, image_lists.keys()[predictions[i]]))

    # Write out the trained graph and labels with the weights stored as constants.
    output_graph_def = graph_util.convert_variables_to_constants(
        sess, graph.as_graph_def(), [final_tensor_name])
    with gfile.FastGFile(output_graph, 'wb') as f:
        f.write(output_graph_def.SerializeToString())
    with gfile.FastGFile(output_labels, 'w') as f:
        f.write('\n'.join(image_lists.keys()) + '\n')


# 直接执行就是测试，需要本地目录先生成好文件
if __name__ == '__main__':
    image_lists = {'giraffe': {'training': ['pic1226_giraffe1_resized.jpg', 'pic17_lakapiaclear2W.gif0_resized.jpg',
                                            'pic2_giraffe.gif0_resized.jpg', 'pic18_giraffe_babies_resized.jpg',
                                            'pic8_9824_giraffe_B_resized.jpg', 'pic1224_giraffe_resized.jpg',
                                            'pic19_giraffe_babies_inset_resized.jpg',
                                            'pic1208_sp_giraffe_social_networks_resized.jpg',
                                            'pic1222_giraffe_by_eraser81112_resized.jpg',
                                            'pic1212_giraffe01_resized.jpg', 'pic1227_859065_2d0aa28b6d_resized.jpg',
                                            'pic7_giraffe_bottom.gif0_resized.jpg',
                                            'pic20_giraffe_video.gif0_resized.jpg', 'pic3_giraffep.gif0_resized.jpg',
                                            'pic1206_Giraffe_485035_small_resized.jpg', 'pic25_01GI14TBR1_resized.jpg',
                                            'pic1211_giraffe.gif0_resized.jpg', 'pic4_giraffe.gif0_resized.jpg'],
                               'testing': ['pic1205_Giraffe_408097_small_resized.jpg',
                                           'pic21_giraffes_pair_inset_resized.jpg'], 'dir': 'Giraffe',
                               'validation': ['pic1221_859065_2d0aa28b6d_resized.jpg',
                                              'pic6_barlogo3.gif0_resized.jpg']}, 'leopard': {
        'training': ['pic1684_big_cat_150_resized.jpg', 'pic4_eclface_resized.jpg',
                     'pic1669_020628_leopard_resized.jpg', 'pic1686_leopard_main_resized.jpg',
                     'pic1677_020614_snowleopard_resized.jpg', 'pic8_jamcub_resized.jpg', 'pic10_lep02_resized.jpg',
                     'pic6_eclspot_resized.jpg', 'pic1664_tn_005_jpg_resized.jpg', 'pic15_sajflbd_resized.jpg',
                     'pic1726_leopard_resized.jpg', 'pic9_lep01_resized.jpg', 'pic5_eclsajbr_resized.jpg',
                     'pic1665_250px-Leopard_resized.jpg', 'pic16_sajlog_resized.jpg', 'pic13_prislog_resized.jpg',
                     'pic1_leopard_resized.jpg', 'pic1685_big_cat_270_resized.jpg', 'pic1682_253feat1_resized.jpg',
                     'pic17_sajstlog_resized.jpg', 'pic2_lepblack_resized.jpg', 'pic1676_snow_leopard_resized.jpg',
                     'pic14_sajbody_resized.jpg', 'pic11_lep03_resized.jpg'], 'testing': [], 'dir': 'Leopard',
        'validation': ['pic1692_lwleocub_resized.jpg', 'pic12_lep04_resized.jpg', 'pic7_eclspry_resized.jpg']}}
    bottleneck_dir = "bottlenecks"
    tf_train(image_lists, bottleneck_dir)
