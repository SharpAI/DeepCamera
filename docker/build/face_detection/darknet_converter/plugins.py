"""plugins.py

I referenced the code from https://github.com/dongfangduoshou123/YoloV3-TensorRT/blob/master/seralizeEngineFromPythonAPI.py
"""


import ctypes

import numpy as np
import tensorrt as trt

try:
    ctypes.cdll.LoadLibrary('./plugins/libyolo_layer.so')
except OSError as e:
    print('ERROR: failed to load ./plugins/libyolo_layer.so.  '
                     'Did you forget to do a "make" in the "./plugins/" '
                     'subdirectory?')
    exit()


def get_input_wh(model_name):
    """Get input_width and input_height of the model."""
    yolo_dim = model_name.split('-')[-1]
    if 'x' in yolo_dim:
        dim_split = yolo_dim.split('x')
        if len(dim_split) != 2:
            raise ValueError('ERROR: bad yolo_dim (%s)!' % yolo_dim)
        w, h = int(dim_split[0]), int(dim_split[1])
    else:
        h = w = int(yolo_dim)
    if h % 32 != 0 or w % 32 != 0:
        raise ValueError('ERROR: bad yolo_dim (%s)!' % yolo_dim)
    return w, h


def get_yolo_whs(model_name, w, h):
    """Get yolo_width and yolo_height for all yolo layers in the model."""
    if 'yolov3' in model_name:
        if 'tiny' in model_name:
            return [[w // 32, h // 32], [w // 16, h // 16]]
        else:
            return [[w // 32, h // 32], [w // 16, h // 16], [w // 8, h // 8]]
    elif 'yolov4' in model_name:
        if 'tiny-3l' in model_name:
            return [[w // 32, h // 32], [w // 16, h // 16], [w // 8, h // 8]]
        elif 'tiny' in model_name:
            return [[w // 32, h // 32], [w // 16, h // 16]]
        else:
            return [[w // 8, h // 8], [w // 16, h // 16], [w // 32, h // 32]]
    else:
        raise ValueError('ERROR: unknown model (%s)!' % args.model)


def verify_classes(model_name, num_classes):
    """Verify 'classes=??' in cfg matches user-specified num_classes."""
    cfg_file_path = model_name + '.cfg'
    with open(cfg_file_path, 'r') as f:
        cfg_lines = f.readlines()
    classes_lines = [l.strip() for l in cfg_lines if l.startswith('classes')]
    classes = [int(l.split('=')[-1]) for l in classes_lines]
    return all([c == num_classes for c in classes])


def get_anchors(model_name):
    """Get anchors of all yolo layers from the cfg file."""
    cfg_file_path = model_name + '.cfg'
    with open(cfg_file_path, 'r') as f:
        cfg_lines = f.readlines()
    yolo_lines = [l.strip() for l in cfg_lines if l.startswith('[yolo]')]
    mask_lines = [l.strip() for l in cfg_lines if l.startswith('mask')]
    anch_lines = [l.strip() for l in cfg_lines if l.startswith('anchors')]
    assert len(mask_lines) == len(yolo_lines)
    assert len(anch_lines) == len(yolo_lines)
    anchor_list = eval('[%s]' % anch_lines[0].split('=')[-1])
    mask_strs = [l.split('=')[-1] for l in mask_lines]
    masks = [eval('[%s]' % s)  for s in mask_strs]
    anchors = []
    for mask in masks:
        curr_anchors = []
        for m in mask:
            curr_anchors.append(anchor_list[m * 2])
            curr_anchors.append(anchor_list[m * 2 + 1])
        anchors.append(curr_anchors)
    return anchors


def get_scales(model_name):
    """Get scale_x_y's of all yolo layers from the cfg file."""
    cfg_file_path = model_name + '.cfg'
    with open(cfg_file_path, 'r') as f:
        cfg_lines = f.readlines()
    yolo_lines = [l.strip() for l in cfg_lines if l.startswith('[yolo]')]
    scale_lines = [l.strip() for l in cfg_lines if l.startswith('scale_x_y')]
    if len(scale_lines) == 0:
        return [1.0] * len(yolo_lines)
    else:
        assert len(scale_lines) == len(yolo_lines)
        return [float(l.split('=')[-1]) for l in scale_lines]


def get_new_coords(model_name):
    """Get new_coords flag of yolo layers from the cfg file."""
    cfg_file_path = model_name + '.cfg'
    with open(cfg_file_path, 'r') as f:
        cfg_lines = f.readlines()
    yolo_lines = [l.strip() for l in cfg_lines if l.startswith('[yolo]')]
    newc_lines = [l.strip() for l in cfg_lines if l.startswith('new_coords')]
    if len(newc_lines) == 0:
        return 0
    else:
        assert len(newc_lines) == len(yolo_lines)
        return int(newc_lines[-1].split('=')[-1])


def get_plugin_creator(plugin_name, logger):
    """Get the TensorRT plugin creator."""
    trt.init_libnvinfer_plugins(logger, '')
    plugin_creator_list = trt.get_plugin_registry().plugin_creator_list
    for c in plugin_creator_list:
        if c.name == plugin_name:
            return c
    return None


def add_yolo_plugins(network, model_name, num_classes, logger):
    """Add yolo plugins into a TensorRT network."""
    input_width, input_height = get_input_wh(model_name)
    yolo_whs = get_yolo_whs(model_name, input_width, input_height)
    if not verify_classes(model_name, num_classes):
        raise ValueError('bad num_classes (%d)' % num_classes)
    anchors = get_anchors(model_name)
    if len(anchors) != len(yolo_whs):
        raise ValueError('bad number of yolo layers: %d vs. %d' %
                         (len(anchors), len(yolo_whs)))
    if network.num_outputs != len(anchors):
        raise ValueError('bad number of network outputs: %d vs. %d' %
                         (network.num_outputs, len(anchors)))
    scales = get_scales(model_name)
    if any([s < 1.0 for s in scales]):
        raise ValueError('bad scale_x_y: %s' % str(scales))
    new_coords = get_new_coords(model_name)

    plugin_creator = get_plugin_creator('YoloLayer_TRT', logger)
    if not plugin_creator:
        raise RuntimeError('cannot get YoloLayer_TRT plugin creator')
    old_tensors = [network.get_output(i) for i in range(network.num_outputs)]
    new_tensors = [None] * network.num_outputs
    for i, old_tensor in enumerate(old_tensors):
        assert input_width  % yolo_whs[i][0] == 0
        assert input_height % yolo_whs[i][1] == 0
        input_multiplier = input_width // yolo_whs[i][0]
        assert input_height // yolo_whs[i][1] == input_multiplier
        new_tensors[i] = network.add_plugin_v2(
            [old_tensor],
            plugin_creator.create_plugin('YoloLayer_TRT', trt.PluginFieldCollection([
                trt.PluginField("yoloWidth", np.array(yolo_whs[i][0], dtype=np.int32), trt.PluginFieldType.INT32),
                trt.PluginField("yoloHeight", np.array(yolo_whs[i][1], dtype=np.int32), trt.PluginFieldType.INT32),
                trt.PluginField("inputMultiplier", np.array(input_multiplier, dtype=np.int32), trt.PluginFieldType.INT32),
                trt.PluginField("newCoords", np.array(new_coords, dtype=np.int32), trt.PluginFieldType.INT32),
                trt.PluginField("numClasses", np.array(num_classes, dtype=np.int32), trt.PluginFieldType.INT32),
                trt.PluginField("numAnchors", np.array(len(anchors[i]) // 2, dtype=np.int32), trt.PluginFieldType.INT32),
                trt.PluginField("anchors", np.ascontiguousarray(anchors[i], dtype=np.float32), trt.PluginFieldType.FLOAT32),
                trt.PluginField("scaleXY", np.array(scales[i], dtype=np.float32), trt.PluginFieldType.FLOAT32),
            ]))
        ).get_output(0)

    for new_tensor in new_tensors:
        network.mark_output(new_tensor)
    for old_tensor in old_tensors:
        network.unmark_output(old_tensor)

    return network
