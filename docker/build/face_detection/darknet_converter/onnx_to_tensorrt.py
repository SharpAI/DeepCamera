# onnx_to_tensorrt.py
#
# Copyright 1993-2019 NVIDIA Corporation.  All rights reserved.
#
# NOTICE TO LICENSEE:
#
# This source code and/or documentation ("Licensed Deliverables") are
# subject to NVIDIA intellectual property rights under U.S. and
# international Copyright laws.
#
# These Licensed Deliverables contained herein is PROPRIETARY and
# CONFIDENTIAL to NVIDIA and is being provided under the terms and
# conditions of a form of NVIDIA software license agreement by and
# between NVIDIA and Licensee ("License Agreement") or electronically
# accepted by Licensee.  Notwithstanding any terms or conditions to
# the contrary in the License Agreement, reproduction or disclosure
# of the Licensed Deliverables to any third party without the express
# written consent of NVIDIA is prohibited.
#
# NOTWITHSTANDING ANY TERMS OR CONDITIONS TO THE CONTRARY IN THE
# LICENSE AGREEMENT, NVIDIA MAKES NO REPRESENTATION ABOUT THE
# SUITABILITY OF THESE LICENSED DELIVERABLES FOR ANY PURPOSE.  IT IS
# PROVIDED "AS IS" WITHOUT EXPRESS OR IMPLIED WARRANTY OF ANY KIND.
# NVIDIA DISCLAIMS ALL WARRANTIES WITH REGARD TO THESE LICENSED
# DELIVERABLES, INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY,
# NONINFRINGEMENT, AND FITNESS FOR A PARTICULAR PURPOSE.
# NOTWITHSTANDING ANY TERMS OR CONDITIONS TO THE CONTRARY IN THE
# LICENSE AGREEMENT, IN NO EVENT SHALL NVIDIA BE LIABLE FOR ANY
# SPECIAL, INDIRECT, INCIDENTAL, OR CONSEQUENTIAL DAMAGES, OR ANY
# DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS,
# WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS
# ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE
# OF THESE LICENSED DELIVERABLES.
#
# U.S. Government End Users.  These Licensed Deliverables are a
# "commercial item" as that term is defined at 48 C.F.R. 2.101 (OCT
# 1995), consisting of "commercial computer software" and "commercial
# computer software documentation" as such terms are used in 48
# C.F.R. 12.212 (SEPT 1995) and is provided to the U.S. Government
# only as a commercial end item.  Consistent with 48 C.F.R.12.212 and
# 48 C.F.R. 227.7202-1 through 227.7202-4 (JUNE 1995), all
# U.S. Government End Users acquire the Licensed Deliverables with
# only those rights set forth herein.
#
# Any use of the Licensed Deliverables in individual and commercial
# software must include, in the user documentation and internal
# comments to the code, the above Disclaimer and U.S. Government End
# Users Notice.
#


from __future__ import print_function

import os
import argparse

import tensorrt as trt

from plugins import get_input_wh, add_yolo_plugins


MAX_BATCH_SIZE = 1


def load_onnx(model_name):
    """Read the ONNX file."""
    onnx_path = '%s.onnx' % model_name
    if not os.path.isfile(onnx_path):
        print('ERROR: file (%s) not found!  You might want to run yolo_to_onnx.py first to generate it.' % onnx_path)
        return None
    else:
        with open(onnx_path, 'rb') as f:
            return f.read()


def set_net_batch(network, batch_size):
    """Set network input batch size.

    The ONNX file might have been generated with a different batch size,
    say, 64.
    """
    if trt.__version__[0] >= '7':
        shape = list(network.get_input(0).shape)
        shape[0] = batch_size
        network.get_input(0).shape = shape
    return network


def build_engine(model_name, category_num, do_int8, dla_core, verbose=False):
    """Build a TensorRT engine from ONNX using the older API."""
    net_w, net_h = get_input_wh(model_name)

    print('Loading the ONNX file...')
    onnx_data = load_onnx(model_name)
    if onnx_data is None:
        return None

    TRT_LOGGER = trt.Logger(trt.Logger.VERBOSE) if verbose else trt.Logger()
    EXPLICIT_BATCH = [] if trt.__version__[0] < '7' else \
        [1 << (int)(trt.NetworkDefinitionCreationFlag.EXPLICIT_BATCH)]
    with trt.Builder(TRT_LOGGER) as builder, builder.create_network(*EXPLICIT_BATCH) as network, trt.OnnxParser(network, TRT_LOGGER) as parser:
        if do_int8 and not builder.platform_has_fast_int8:
            raise RuntimeError('INT8 not supported on this platform')
        if not parser.parse(onnx_data):
            print('ERROR: Failed to parse the ONNX file.')
            for error in range(parser.num_errors):
                print(parser.get_error(error))
            return None
        network = set_net_batch(network, MAX_BATCH_SIZE)

        print('Adding yolo_layer plugins...')
        network = add_yolo_plugins(
            network, model_name, category_num, TRT_LOGGER)

        print('Building an engine.  This would take a while...')
        print('(Use "--verbose" or "-v" to enable verbose logging.)')
        if trt.__version__[0] < '7':  # older API: build_cuda_engine()
            if dla_core >= 0:
                raise RuntimeError('DLA core not supported by old API')
            builder.max_batch_size = MAX_BATCH_SIZE
            builder.max_workspace_size = 1 << 30
            builder.fp16_mode = True  # alternative: builder.platform_has_fast_fp16
            if do_int8:
                from calibrator import YOLOEntropyCalibrator
                builder.int8_mode = True
                builder.int8_calibrator = YOLOEntropyCalibrator(
                    'calib_images', (net_h, net_w), 'calib_%s.bin' % model_name)
            engine = builder.build_cuda_engine(network)
        else:  # new API: build_engine() with builder config
            builder.max_batch_size = MAX_BATCH_SIZE
            config = builder.create_builder_config()
            config.max_workspace_size = 1 << 30
            config.set_flag(trt.BuilderFlag.GPU_FALLBACK)
            if True:
                config.set_flag(trt.BuilderFlag.FP16)
                print("building fp16 engine")
            else:
                print('building fp32 engine')
            profile = builder.create_optimization_profile()
            profile.set_shape(
                '000_net',                          # input tensor name
                (MAX_BATCH_SIZE, 3, net_h, net_w),  # min shape
                (MAX_BATCH_SIZE, 3, net_h, net_w),  # opt shape
                (MAX_BATCH_SIZE, 3, net_h, net_w))  # max shape
            config.add_optimization_profile(profile)
            if do_int8:
                from calibrator import YOLOEntropyCalibrator
                config.set_flag(trt.BuilderFlag.INT8)
                config.int8_calibrator = YOLOEntropyCalibrator(
                    'calib_images', (net_h, net_w),
                    'calib_%s.bin' % model_name)
                config.set_calibration_profile(profile)
            if dla_core >= 0:
                config.default_device_type = trt.DeviceType.DLA
                config.DLA_core = dla_core
                config.set_flag(trt.BuilderFlag.STRICT_TYPES)
                print('Using DLA core %d.' % dla_core)
            engine = builder.build_engine(network, config)

        if engine is not None:
            print('Completed creating engine.')
        return engine


def main():
    """Create a TensorRT engine for ONNX-based YOLO."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-v', '--verbose', action='store_true',
        help='enable verbose output (for debugging)')
    parser.add_argument(
        '-c', '--category_num', type=int, default=80,
        help='number of object categories [80]')
    parser.add_argument(
        '-m', '--model', type=str, required=True,
        help=('[yolov3|yolov3-tiny|yolov3-spp|yolov4|yolov4-tiny]-'
              '[{dimension}], where dimension could be a single '
              'number (e.g. 288, 416, 608) or WxH (e.g. 416x256)'))
    parser.add_argument(
        '--int8', action='store_true',
        help='build INT8 TensorRT engine')
    parser.add_argument(
        '--dla_core', type=int, default=-1,
        help='id of DLA core for inference (0 ~ N-1)')
    args = parser.parse_args()

    engine = build_engine(
        args.model, args.category_num, args.int8, args.dla_core, args.verbose)
    if engine is None:
        raise SystemExit('ERROR: failed to build the TensorRT engine!')

    engine_path = '%s.trt' % args.model
    with open(engine_path, 'wb') as f:
        f.write(engine.serialize())
    print('Serialized the TensorRT engine to file: %s' % engine_path)


if __name__ == '__main__':
    main()
