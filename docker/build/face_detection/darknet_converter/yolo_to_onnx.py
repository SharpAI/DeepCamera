# yolo_to_onnx.py
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
import sys
import hashlib
import argparse
from collections import OrderedDict

import numpy as np
import onnx
from onnx import helper, TensorProto

from plugins import verify_classes, get_input_wh


MAX_BATCH_SIZE = 1


class DarkNetParser(object):
    """Definition of a parser for DarkNet-based YOLO model."""

    def __init__(self, supported_layers):
        """Initializes a DarkNetParser object.

        Keyword argument:
        supported_layers -- a string list of supported layers in DarkNet naming convention,
        parameters are only added to the class dictionary if a parsed layer is included.
        """

        # A list of YOLO layers containing dictionaries with all layer
        # parameters:
        self.layer_configs = OrderedDict()
        self.supported_layers = supported_layers
        self.layer_counter = 0

    def parse_cfg_file(self, cfg_file_path):
        """Takes the yolov?.cfg file and parses it layer by layer,
        appending each layer's parameters as a dictionary to layer_configs.

        Keyword argument:
        cfg_file_path
        """
        with open(cfg_file_path, 'r') as cfg_file:
            remainder = cfg_file.read()
            while remainder is not None:
                layer_dict, layer_name, remainder = self._next_layer(remainder)
                if layer_dict is not None:
                    self.layer_configs[layer_name] = layer_dict
        return self.layer_configs

    def _next_layer(self, remainder):
        """Takes in a string and segments it by looking for DarkNet delimiters.
        Returns the layer parameters and the remaining string after the last delimiter.
        Example for the first Conv layer in yolo.cfg ...

        [convolutional]
        batch_normalize=1
        filters=32
        size=3
        stride=1
        pad=1
        activation=leaky

        ... becomes the following layer_dict return value:
        {'activation': 'leaky', 'stride': 1, 'pad': 1, 'filters': 32,
        'batch_normalize': 1, 'type': 'convolutional', 'size': 3}.

        '001_convolutional' is returned as layer_name, and all lines that follow in yolo.cfg
        are returned as the next remainder.

        Keyword argument:
        remainder -- a string with all raw text after the previously parsed layer
        """
        remainder = remainder.split('[', 1)
        while len(remainder[0]) > 0 and remainder[0][-1] == '#':
            # '#[...' case (the left bracket is proceeded by a pound sign),
            # assuming this layer is commented out, so go find the next '['
            remainder = remainder[1].split('[', 1)
        if len(remainder) == 2:
            remainder = remainder[1]
        else:
            # no left bracket found in remainder
            return None, None, None
        remainder = remainder.split(']', 1)
        if len(remainder) == 2:
            layer_type, remainder = remainder
        else:
            # no right bracket
            raise ValueError('no closing bracket!')
        if layer_type not in self.supported_layers:
            raise ValueError('%s layer not supported!' % layer_type)

        out = remainder.split('\n[', 1)
        if len(out) == 2:
            layer_param_block, remainder = out[0], '[' + out[1]
        else:
            layer_param_block, remainder = out[0], ''
        layer_param_lines = layer_param_block.split('\n')
        # remove empty lines
        layer_param_lines = [l.lstrip() for l in layer_param_lines if l.lstrip()]
        # don't parse yolo layers
        if layer_type == 'yolo':  layer_param_lines = []
        skip_params = ['steps', 'scales'] if layer_type == 'net' else []
        layer_name = str(self.layer_counter).zfill(3) + '_' + layer_type
        layer_dict = dict(type=layer_type)
        for param_line in layer_param_lines:
            param_line = param_line.split('#')[0]
            if not param_line:  continue
            assert '[' not in param_line
            param_type, param_value = self._parse_params(param_line, skip_params)
            layer_dict[param_type] = param_value
        self.layer_counter += 1
        return layer_dict, layer_name, remainder

    def _parse_params(self, param_line, skip_params=None):
        """Identifies the parameters contained in one of the cfg file and returns
        them in the required format for each parameter type, e.g. as a list, an int or a float.

        Keyword argument:
        param_line -- one parsed line within a layer block
        """
        param_line = param_line.replace(' ', '')
        param_type, param_value_raw = param_line.split('=')
        assert param_value_raw
        param_value = None
        if skip_params and param_type in skip_params:
            param_type = None
        elif param_type == 'layers':
            layer_indexes = list()
            for index in param_value_raw.split(','):
                layer_indexes.append(int(index))
            param_value = layer_indexes
        elif isinstance(param_value_raw, str) and not param_value_raw.isalpha():
            condition_param_value_positive = param_value_raw.isdigit()
            condition_param_value_negative = param_value_raw[0] == '-' and \
                param_value_raw[1:].isdigit()
            if condition_param_value_positive or condition_param_value_negative:
                param_value = int(param_value_raw)
            else:
                param_value = float(param_value_raw)
        else:
            param_value = str(param_value_raw)
        return param_type, param_value


class MajorNodeSpecs(object):
    """Helper class used to store the names of ONNX output names,
    corresponding to the output of a DarkNet layer and its output channels.
    Some DarkNet layers are not created and there is no corresponding ONNX node,
    but we still need to track them in order to set up skip connections.
    """

    def __init__(self, name, channels):
        """ Initialize a MajorNodeSpecs object.

        Keyword arguments:
        name -- name of the ONNX node
        channels -- number of output channels of this node
        """
        self.name = name
        self.channels = channels
        self.created_onnx_node = False
        if name is not None and isinstance(channels, int) and channels > 0:
            self.created_onnx_node = True


class ConvParams(object):
    """Helper class to store the hyper parameters of a Conv layer,
    including its prefix name in the ONNX graph and the expected dimensions
    of weights for convolution, bias, and batch normalization.

    Additionally acts as a wrapper for generating safe names for all
    weights, checking on feasible combinations.
    """

    def __init__(self, node_name, batch_normalize, conv_weight_dims):
        """Constructor based on the base node name (e.g. 101_convolutional), the batch
        normalization setting, and the convolutional weights shape.

        Keyword arguments:
        node_name -- base name of this YOLO convolutional layer
        batch_normalize -- bool value if batch normalization is used
        conv_weight_dims -- the dimensions of this layer's convolutional weights
        """
        self.node_name = node_name
        self.batch_normalize = batch_normalize
        assert len(conv_weight_dims) == 4
        self.conv_weight_dims = conv_weight_dims

    def generate_param_name(self, param_category, suffix):
        """Generates a name based on two string inputs,
        and checks if the combination is valid."""
        assert suffix
        assert param_category in ['bn', 'conv']
        assert(suffix in ['scale', 'mean', 'var', 'weights', 'bias'])
        if param_category == 'bn':
            assert self.batch_normalize
            assert suffix in ['scale', 'bias', 'mean', 'var']
        elif param_category == 'conv':
            assert suffix in ['weights', 'bias']
            if suffix == 'bias':
                assert not self.batch_normalize
        param_name = self.node_name + '_' + param_category + '_' + suffix
        return param_name

class UpsampleParams(object):
    #Helper class to store the scale parameter for an Upsample node.

    def __init__(self, node_name, value):
        """Constructor based on the base node name (e.g. 86_Upsample),
        and the value of the scale input tensor.

        Keyword arguments:
        node_name -- base name of this YOLO Upsample layer
        value -- the value of the scale input to the Upsample layer as a numpy array
        """
        self.node_name = node_name
        self.value = value

    def generate_param_name(self):
        """Generates the scale parameter name for the Upsample node."""
        param_name = self.node_name + '_' + 'scale'
        return param_name

class WeightLoader(object):
    """Helper class used for loading the serialized weights of a binary file stream
    and returning the initializers and the input tensors required for populating
    the ONNX graph with weights.
    """

    def __init__(self, weights_file_path):
        """Initialized with a path to the YOLO .weights file.

        Keyword argument:
        weights_file_path -- path to the weights file.
        """
        self.weights_file = self._open_weights_file(weights_file_path)

    def load_upsample_scales(self, upsample_params):
        """Returns the initializers with the value of the scale input
        tensor given by upsample_params.

        Keyword argument:
        upsample_params -- a UpsampleParams object
        """
        initializer = list()
        inputs = list()
        name = upsample_params.generate_param_name()
        shape = upsample_params.value.shape
        data = upsample_params.value
        scale_init = helper.make_tensor(
            name, TensorProto.FLOAT, shape, data)
        scale_input = helper.make_tensor_value_info(
            name, TensorProto.FLOAT, shape)
        initializer.append(scale_init)
        inputs.append(scale_input)
        return initializer, inputs


    def load_conv_weights(self, conv_params):
        """Returns the initializers with weights from the weights file and
        the input tensors of a convolutional layer for all corresponding ONNX nodes.

        Keyword argument:
        conv_params -- a ConvParams object
        """
        initializer = list()
        inputs = list()
        if conv_params.batch_normalize:
            bias_init, bias_input = self._create_param_tensors(
                conv_params, 'bn', 'bias')
            bn_scale_init, bn_scale_input = self._create_param_tensors(
                conv_params, 'bn', 'scale')
            bn_mean_init, bn_mean_input = self._create_param_tensors(
                conv_params, 'bn', 'mean')
            bn_var_init, bn_var_input = self._create_param_tensors(
                conv_params, 'bn', 'var')
            initializer.extend(
                [bn_scale_init, bias_init, bn_mean_init, bn_var_init])
            inputs.extend([bn_scale_input, bias_input,
                           bn_mean_input, bn_var_input])
        else:
            bias_init, bias_input = self._create_param_tensors(
                conv_params, 'conv', 'bias')
            initializer.append(bias_init)
            inputs.append(bias_input)
        conv_init, conv_input = self._create_param_tensors(
            conv_params, 'conv', 'weights')
        initializer.append(conv_init)
        inputs.append(conv_input)
        return initializer, inputs

    def _open_weights_file(self, weights_file_path):
        """Opens a YOLO DarkNet file stream and skips the header.

        Keyword argument:
        weights_file_path -- path to the weights file.
        """
        weights_file = open(weights_file_path, 'rb')
        length_header = 5
        np.ndarray(shape=(length_header, ), dtype='int32',
                   buffer=weights_file.read(length_header * 4))
        return weights_file

    def _create_param_tensors(self, conv_params, param_category, suffix):
        """Creates the initializers with weights from the weights file together with
        the input tensors.

        Keyword arguments:
        conv_params -- a ConvParams object
        param_category -- the category of parameters to be created ('bn' or 'conv')
        suffix -- a string determining the sub-type of above param_category (e.g.,
        'weights' or 'bias')
        """
        param_name, param_data, param_data_shape = self._load_one_param_type(
            conv_params, param_category, suffix)

        initializer_tensor = helper.make_tensor(
            param_name, TensorProto.FLOAT, param_data_shape, param_data)
        input_tensor = helper.make_tensor_value_info(
            param_name, TensorProto.FLOAT, param_data_shape)
        return initializer_tensor, input_tensor

    def _load_one_param_type(self, conv_params, param_category, suffix):
        """Deserializes the weights from a file stream in the DarkNet order.

        Keyword arguments:
        conv_params -- a ConvParams object
        param_category -- the category of parameters to be created ('bn' or 'conv')
        suffix -- a string determining the sub-type of above param_category (e.g.,
        'weights' or 'bias')
        """
        param_name = conv_params.generate_param_name(param_category, suffix)
        channels_out, channels_in, filter_h, filter_w = conv_params.conv_weight_dims
        if param_category == 'bn':
            param_shape = [channels_out]
        elif param_category == 'conv':
            if suffix == 'weights':
                param_shape = [channels_out, channels_in, filter_h, filter_w]
            elif suffix == 'bias':
                param_shape = [channels_out]
        param_size = np.product(np.array(param_shape))
        param_data = np.ndarray(
            shape=param_shape,
            dtype='float32',
            buffer=self.weights_file.read(param_size * 4))
        param_data = param_data.flatten().astype(float)
        return param_name, param_data, param_shape


class GraphBuilderONNX(object):
    """Class for creating an ONNX graph from a previously generated list of layer dictionaries."""

    def __init__(self, model_name, output_tensors):
        """Initialize with all DarkNet default parameters used creating
        YOLO, and specify the output tensors as an OrderedDict for their
        output dimensions with their names as keys.

        Keyword argument:
        output_tensors -- the output tensors as an OrderedDict containing the keys'
        output dimensions
        """
        self.model_name = model_name
        self.output_tensors = output_tensors
        self._nodes = list()
        self.graph_def = None
        self.input_tensor = None
        self.epsilon_bn = 1e-5
        self.momentum_bn = 0.99
        self.alpha_lrelu = 0.1
        self.param_dict = OrderedDict()
        self.major_node_specs = list()
        self.batch_size = MAX_BATCH_SIZE
        self.route_spec = 0  # keeping track of the current active 'route'

    def build_onnx_graph(
            self,
            layer_configs,
            weights_file_path,
            verbose=True):
        """Iterate over all layer configs (parsed from the DarkNet
        representation of YOLO), create an ONNX graph, populate it with
        weights from the weights file and return the graph definition.

        Keyword arguments:
        layer_configs -- an OrderedDict object with all parsed layers' configurations
        weights_file_path -- location of the weights file
        verbose -- toggles if the graph is printed after creation (default: True)
        """
        for layer_name in layer_configs.keys():
            layer_dict = layer_configs[layer_name]
            major_node_specs = self._make_onnx_node(layer_name, layer_dict)
            if major_node_specs.name is not None:
                self.major_node_specs.append(major_node_specs)
        # remove dummy 'route' and 'yolo' nodes
        self.major_node_specs = [node for node in self.major_node_specs
                                      if 'dummy' not in node.name]
        outputs = list()
        for tensor_name in self.output_tensors.keys():
            output_dims = [self.batch_size, ] + \
                self.output_tensors[tensor_name]
            output_tensor = helper.make_tensor_value_info(
                tensor_name, TensorProto.FLOAT, output_dims)
            outputs.append(output_tensor)
        inputs = [self.input_tensor]
        weight_loader = WeightLoader(weights_file_path)
        initializer = list()
        # If a layer has parameters, add them to the initializer and input lists.
        for layer_name in self.param_dict.keys():
            _, layer_type = layer_name.split('_', 1)
            params = self.param_dict[layer_name]
            if layer_type == 'convolutional':
                initializer_layer, inputs_layer = weight_loader.load_conv_weights(
                    params)
                initializer.extend(initializer_layer)
                inputs.extend(inputs_layer)
            elif layer_type == 'upsample':
                initializer_layer, inputs_layer = weight_loader.load_upsample_scales(
                    params)
                initializer.extend(initializer_layer)
                inputs.extend(inputs_layer)
        del weight_loader
        self.graph_def = helper.make_graph(
            nodes=self._nodes,
            name=self.model_name,
            inputs=inputs,
            outputs=outputs,
            initializer=initializer
        )
        if verbose:
            print(helper.printable_graph(self.graph_def))
        model_def = helper.make_model(self.graph_def,
                                      producer_name='NVIDIA TensorRT sample')
        return model_def

    def _make_onnx_node(self, layer_name, layer_dict):
        """Take in a layer parameter dictionary, choose the correct function for
        creating an ONNX node and store the information important to graph creation
        as a MajorNodeSpec object.

        Keyword arguments:
        layer_name -- the layer's name (also the corresponding key in layer_configs)
        layer_dict -- a layer parameter dictionary (one element of layer_configs)
        """
        layer_type = layer_dict['type']
        if self.input_tensor is None:
            if layer_type == 'net':
                major_node_output_name, major_node_output_channels = self._make_input_tensor(
                    layer_name, layer_dict)
                major_node_specs = MajorNodeSpecs(major_node_output_name,
                                                  major_node_output_channels)
            else:
                raise ValueError('The first node has to be of type "net".')
        else:
            node_creators = dict()
            node_creators['convolutional'] = self._make_conv_node
            node_creators['maxpool'] = self._make_maxpool_node
            node_creators['shortcut'] = self._make_shortcut_node
            node_creators['route'] = self._make_route_node
            node_creators['upsample'] = self._make_upsample_node
            node_creators['yolo'] = self._make_yolo_node

            if layer_type in node_creators.keys():
                major_node_output_name, major_node_output_channels = \
                    node_creators[layer_type](layer_name, layer_dict)
                major_node_specs = MajorNodeSpecs(major_node_output_name,
                                                  major_node_output_channels)
            else:
                raise TypeError('layer of type %s not supported' % layer_type)
        return major_node_specs

    def _make_input_tensor(self, layer_name, layer_dict):
        """Create an ONNX input tensor from a 'net' layer and store the batch size.

        Keyword arguments:
        layer_name -- the layer's name (also the corresponding key in layer_configs)
        layer_dict -- a layer parameter dictionary (one element of layer_configs)
        """
        #batch_size = layer_dict['batch']
        channels = layer_dict['channels']
        height = layer_dict['height']
        width = layer_dict['width']
        #self.batch_size = batch_size
        input_tensor = helper.make_tensor_value_info(
            str(layer_name), TensorProto.FLOAT, [
                self.batch_size, channels, height, width])
        self.input_tensor = input_tensor
        return layer_name, channels

    def _get_previous_node_specs(self, target_index=0):
        """Get a previously ONNX node.

        Target index can be passed for jumping to a specific index.

        Keyword arguments:
        target_index -- optional for jumping to a specific index,
                        default: 0 for the previous element, while
                        taking 'route' spec into account
        """
        if target_index == 0:
            if self.route_spec != 0:
                previous_node = self.major_node_specs[self.route_spec]
                assert 'dummy' not in previous_node.name
                self.route_spec = 0
            else:
                previous_node = self.major_node_specs[-1]
        else:
            previous_node = self.major_node_specs[target_index]
        assert previous_node.created_onnx_node
        return previous_node

    def _make_conv_node(self, layer_name, layer_dict):
        """Create an ONNX Conv node with optional batch normalization and
        activation nodes.

        Keyword arguments:
        layer_name -- the layer's name (also the corresponding key in layer_configs)
        layer_dict -- a layer parameter dictionary (one element of layer_configs)
        """
        previous_node_specs = self._get_previous_node_specs()
        inputs = [previous_node_specs.name]
        previous_channels = previous_node_specs.channels
        kernel_size = layer_dict['size']
        stride = layer_dict['stride']
        filters = layer_dict['filters']
        batch_normalize = False
        if 'batch_normalize' in layer_dict.keys(
        ) and layer_dict['batch_normalize'] == 1:
            batch_normalize = True

        kernel_shape = [kernel_size, kernel_size]
        weights_shape = [filters, previous_channels] + kernel_shape
        conv_params = ConvParams(layer_name, batch_normalize, weights_shape)

        strides = [stride, stride]
        dilations = [1, 1]
        weights_name = conv_params.generate_param_name('conv', 'weights')
        inputs.append(weights_name)
        if not batch_normalize:
            bias_name = conv_params.generate_param_name('conv', 'bias')
            inputs.append(bias_name)

        conv_node = helper.make_node(
            'Conv',
            inputs=inputs,
            outputs=[layer_name],
            kernel_shape=kernel_shape,
            strides=strides,
            auto_pad='SAME_LOWER',
            dilations=dilations,
            name=layer_name
        )
        self._nodes.append(conv_node)
        inputs = [layer_name]
        layer_name_output = layer_name

        if batch_normalize:
            layer_name_bn = layer_name + '_bn'
            bn_param_suffixes = ['scale', 'bias', 'mean', 'var']
            for suffix in bn_param_suffixes:
                bn_param_name = conv_params.generate_param_name('bn', suffix)
                inputs.append(bn_param_name)
            batchnorm_node = helper.make_node(
                'BatchNormalization',
                inputs=inputs,
                outputs=[layer_name_bn],
                epsilon=self.epsilon_bn,
                momentum=self.momentum_bn,
                name=layer_name_bn
            )
            self._nodes.append(batchnorm_node)
            inputs = [layer_name_bn]
            layer_name_output = layer_name_bn

        if layer_dict['activation'] == 'leaky':
            layer_name_lrelu = layer_name + '_lrelu'

            lrelu_node = helper.make_node(
                'LeakyRelu',
                inputs=inputs,
                outputs=[layer_name_lrelu],
                name=layer_name_lrelu,
                alpha=self.alpha_lrelu
            )
            self._nodes.append(lrelu_node)
            inputs = [layer_name_lrelu]
            layer_name_output = layer_name_lrelu
        elif layer_dict['activation'] == 'mish':
            layer_name_softplus = layer_name + '_softplus'
            layer_name_tanh = layer_name + '_tanh'
            layer_name_mish = layer_name + '_mish'

            softplus_node = helper.make_node(
                'Softplus',
                inputs=inputs,
                outputs=[layer_name_softplus],
                name=layer_name_softplus
            )
            self._nodes.append(softplus_node)
            tanh_node = helper.make_node(
                'Tanh',
                inputs=[layer_name_softplus],
                outputs=[layer_name_tanh],
                name=layer_name_tanh
            )
            self._nodes.append(tanh_node)

            inputs.append(layer_name_tanh)
            mish_node = helper.make_node(
                'Mul',
                inputs=inputs,
                outputs=[layer_name_mish],
                name=layer_name_mish
            )
            self._nodes.append(mish_node)

            inputs = [layer_name_mish]
            layer_name_output = layer_name_mish
        elif layer_dict['activation'] == 'logistic':
            layer_name_lgx = layer_name + '_lgx'

            lgx_node = helper.make_node(
                'Sigmoid',
                inputs=inputs,
                outputs=[layer_name_lgx],
                name=layer_name_lgx
            )
            self._nodes.append(lgx_node)
            inputs = [layer_name_lgx]
            layer_name_output = layer_name_lgx
        elif layer_dict['activation'] == 'linear':
            pass
        else:
            raise TypeError('%s activation not supported' % layer_dict['activation'])

        self.param_dict[layer_name] = conv_params
        return layer_name_output, filters

    def _make_shortcut_node(self, layer_name, layer_dict):
        """Create an ONNX Add node with the shortcut properties from
        the DarkNet-based graph.

        Keyword arguments:
        layer_name -- the layer's name (also the corresponding key in layer_configs)
        layer_dict -- a layer parameter dictionary (one element of layer_configs)
        """
        shortcut_index = layer_dict['from']
        activation = layer_dict['activation']
        assert activation == 'linear'

        first_node_specs = self._get_previous_node_specs()
        second_node_specs = self._get_previous_node_specs(
            target_index=shortcut_index)
        assert first_node_specs.channels == second_node_specs.channels
        channels = first_node_specs.channels
        inputs = [first_node_specs.name, second_node_specs.name]
        shortcut_node = helper.make_node(
            'Add',
            inputs=inputs,
            outputs=[layer_name],
            name=layer_name,
        )
        self._nodes.append(shortcut_node)
        return layer_name, channels

    def _make_route_node(self, layer_name, layer_dict):
        """If the 'layers' parameter from the DarkNet configuration is only one index, continue
        node creation at the indicated (negative) index. Otherwise, create an ONNX Concat node
        with the route properties from the DarkNet-based graph.

        Keyword arguments:
        layer_name -- the layer's name (also the corresponding key in layer_configs)
        layer_dict -- a layer parameter dictionary (one element of layer_configs)
        """
        route_node_indexes = layer_dict['layers']
        if len(route_node_indexes) == 1:
            if 'groups' in layer_dict.keys():
                # for CSPNet-kind of architecture
                assert 'group_id' in layer_dict.keys()
                groups = layer_dict['groups']
                group_id = int(layer_dict['group_id'])
                assert group_id < groups
                index = route_node_indexes[0]
                if index > 0:
                    # +1 for input node (same reason as below)
                    index += 1
                route_node_specs = self._get_previous_node_specs(
                    target_index=index)
                assert route_node_specs.channels % groups == 0
                channels = route_node_specs.channels // groups

                outputs = [layer_name + '_dummy%d' % i for i in range(groups)]
                outputs[group_id] = layer_name
                route_node = helper.make_node(
                    'Split',
                    axis=1,
                    split=[channels] * groups,
                    inputs=[route_node_specs.name],
                    outputs=outputs,
                    name=layer_name,
                )
                self._nodes.append(route_node)
            else:
                if route_node_indexes[0] < 0:
                    # route should skip self, thus -1
                    self.route_spec = route_node_indexes[0] - 1
                elif route_node_indexes[0] > 0:
                    # +1 for input node (same reason as below)
                    self.route_spec = route_node_indexes[0] + 1
                # This dummy route node would be removed in the end.
                layer_name = layer_name + '_dummy'
                channels = 1
        else:
            assert 'groups' not in layer_dict.keys(), \
                'groups not implemented for multiple-input route layer!'
            inputs = list()
            channels = 0
            for index in route_node_indexes:
                if index > 0:
                    # Increment by one because we count the input as
                    # a node (DarkNet does not)
                    index += 1
                route_node_specs = self._get_previous_node_specs(
                    target_index=index)
                inputs.append(route_node_specs.name)
                channels += route_node_specs.channels
            assert inputs
            assert channels > 0

            route_node = helper.make_node(
                'Concat',
                axis=1,
                inputs=inputs,
                outputs=[layer_name],
                name=layer_name,
            )
            self._nodes.append(route_node)
        return layer_name, channels

    def _make_upsample_node(self, layer_name, layer_dict):
        """Create an ONNX Upsample node with the properties from
        the DarkNet-based graph.

        Keyword arguments:
        layer_name -- the layer's name (also the corresponding key in layer_configs)
        layer_dict -- a layer parameter dictionary (one element of layer_configs)
        """
        upsample_factor = float(layer_dict['stride'])
        # Create the scales array with node parameters
        scales = np.array([1.0, 1.0, upsample_factor, upsample_factor]).astype(np.float32)
        previous_node_specs = self._get_previous_node_specs()
        inputs = [previous_node_specs.name]

        channels = previous_node_specs.channels
        assert channels > 0
        upsample_params = UpsampleParams(layer_name, scales)
        scales_name = upsample_params.generate_param_name()
        # For ONNX opset >= 9, the Upsample node takes the scales array
        # as an input.
        inputs.append(scales_name)

        upsample_node = helper.make_node(
            'Upsample',
            mode='nearest',
            inputs=inputs,
            outputs=[layer_name],
            name=layer_name,
        )
        self._nodes.append(upsample_node)
        self.param_dict[layer_name] = upsample_params
        return layer_name, channels

    def _make_maxpool_node(self, layer_name, layer_dict):
        """Create an ONNX Maxpool node with the properties from
        the DarkNet-based graph.

        Keyword arguments:
        layer_name -- the layer's name (also the corresponding key in layer_configs)
        layer_dict -- a layer parameter dictionary (one element of layer_configs)
        """
        stride = layer_dict['stride']
        kernel_size = layer_dict['size']
        previous_node_specs = self._get_previous_node_specs()
        inputs = [previous_node_specs.name]
        channels = previous_node_specs.channels
        kernel_shape = [kernel_size, kernel_size]
        strides = [stride, stride]
        assert channels > 0
        maxpool_node = helper.make_node(
            'MaxPool',
            inputs=inputs,
            outputs=[layer_name],
            kernel_shape=kernel_shape,
            strides=strides,
            auto_pad='SAME_UPPER',
            name=layer_name,
        )
        self._nodes.append(maxpool_node)
        return layer_name, channels

    def _make_yolo_node(self, layer_name, layer_dict):
        """Create an ONNX Yolo node.

        These are dummy nodes which would be removed in the end.
        """
        channels = 1
        return layer_name + '_dummy', channels


def generate_md5_checksum(local_path):
    """Returns the MD5 checksum of a local file.

    Keyword argument:
    local_path -- path of the file whose checksum shall be generated
    """
    with open(local_path, 'rb') as local_file:
        data = local_file.read()
        return hashlib.md5(data).hexdigest()


def main():
    """Run the DarkNet-to-ONNX conversion for YOLO (v3 or v4)."""
    #if sys.version_info[0] < 3:
    #    raise SystemExit('ERROR: This modified version of yolov3_to_onnx.py '
    #                     'script is only compatible with python3...')

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-c', '--category_num', type=int, default=80,
        help='number of object categories [80]')
    parser.add_argument(
        '-m', '--model', type=str, required=True,
        help=('[yolov3|yolov3-tiny|yolov3-spp|yolov4|yolov4-tiny]-'
              '[{dimension}], where dimension could be a single '
              'number (e.g. 288, 416, 608) or WxH (e.g. 416x256)'))
    args = parser.parse_args()
    if args.category_num <= 0:
        raise SystemExit('ERROR: bad category_num (%d)!' % args.category_num)

    cfg_file_path = '%s.cfg' % args.model
    if not os.path.isfile(cfg_file_path):
        raise SystemExit('ERROR: file (%s) not found!' % cfg_file_path)
    weights_file_path = '%s.weights' % args.model
    if not os.path.isfile(weights_file_path):
        raise SystemExit('ERROR: file (%s) not found!' % weights_file_path)
    output_file_path = '%s.onnx' % args.model

    if not verify_classes(args.model, args.category_num):
        raise SystemExit('ERROR: bad category_num (%d)' % args.category_num)

    # Derive yolo input width/height from model name.
    # For example, "yolov4-416x256" -> width=416, height=256
    w, h = get_input_wh(args.model)

    # These are the only layers DarkNetParser will extract parameters
    # from.  The three layers of type 'yolo' are not parsed in detail
    # because they are included in the post-processing later.
    supported_layers = ['net', 'convolutional', 'maxpool',
                        'shortcut', 'route', 'upsample', 'yolo']

    # Create a DarkNetParser object, and the use it to generate an
    # OrderedDict with all layer's configs from the cfg file.
    print('Parsing DarkNet cfg file...')
    parser = DarkNetParser(supported_layers)
    layer_configs = parser.parse_cfg_file(cfg_file_path)

    # We do not need the parser anymore after we got layer_configs.
    del parser

    # In above layer_config, there are three outputs that we need to
    # know the output shape of (in CHW format).
    output_tensor_dims = OrderedDict()
    c = (args.category_num + 5) * 3
    if 'yolov3' in args.model:
        if 'tiny' in args.model:
            output_tensor_dims['016_convolutional'] = [c, h // 32, w // 32]
            output_tensor_dims['023_convolutional'] = [c, h // 16, w // 16]
        elif 'spp' in args.model:
            output_tensor_dims['089_convolutional'] = [c, h // 32, w // 32]
            output_tensor_dims['101_convolutional'] = [c, h // 16, w // 16]
            output_tensor_dims['113_convolutional'] = [c, h //  8, w //  8]
        else:
            output_tensor_dims['082_convolutional'] = [c, h // 32, w // 32]
            output_tensor_dims['094_convolutional'] = [c, h // 16, w // 16]
            output_tensor_dims['106_convolutional'] = [c, h //  8, w //  8]
    elif 'yolov4' in args.model:
        if 'tiny-3l' in args.model:
            output_tensor_dims['030_convolutional'] = [c, h // 32, w // 32]
            output_tensor_dims['037_convolutional'] = [c, h // 16, w // 16]
            output_tensor_dims['044_convolutional'] = [c, h // 8, w // 8]
        elif 'yolov4x-mish' in args.model:
            output_tensor_dims['168_convolutional_lgx'] = [c, h //  8, w //  8]
            output_tensor_dims['185_convolutional_lgx'] = [c, h // 16, w // 16]
            output_tensor_dims['202_convolutional_lgx'] = [c, h // 32, w // 32]
        elif 'yolov4-csp' in args.model:
            output_tensor_dims['144_convolutional_lgx'] = [c, h //  8, w //  8]
            output_tensor_dims['159_convolutional_lgx'] = [c, h // 16, w // 16]
            output_tensor_dims['174_convolutional_lgx'] = [c, h // 32, w // 32]
        elif 'tiny' in args.model:
            output_tensor_dims['030_convolutional'] = [c, h // 32, w // 32]
            output_tensor_dims['037_convolutional'] = [c, h // 16, w // 16]
        else:
            output_tensor_dims['139_convolutional'] = [c, h //  8, w //  8]
            output_tensor_dims['150_convolutional'] = [c, h // 16, w // 16]
            output_tensor_dims['161_convolutional'] = [c, h // 32, w // 32]
    else:
        raise SystemExit('ERROR: unknown model (%s)!' % args.model)

    # Create a GraphBuilderONNX object with the specified output tensor
    # dimensions.
    print('Building ONNX graph...')
    builder = GraphBuilderONNX(args.model, output_tensor_dims)

    # Now generate an ONNX graph with weights from the previously parsed
    # layer configurations and the weights file.
    yolo_model_def = builder.build_onnx_graph(
        layer_configs=layer_configs,
        weights_file_path=weights_file_path,
        verbose=True)

    # Once we have the model definition, we do not need the builder anymore.
    del builder

    # Perform a sanity check on the ONNX model definition.
    print('Checking ONNX model...')
    onnx.checker.check_model(yolo_model_def)

    # Serialize the generated ONNX graph to this file.
    print('Saving ONNX file...')
    onnx.save(yolo_model_def, output_file_path)

    print('Done.')


if __name__ == '__main__':
    main()
