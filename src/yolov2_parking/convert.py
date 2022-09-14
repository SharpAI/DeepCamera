import sys
import numpy
import _convert

from cffi import FFI

ffi = FFI()

# window size 2
# RGB array (3D)

my_input = numpy.array(
    [
        [[1,2,3],[5,6,7],[4,5,6],[6,4,5]],
        [[4,6,3],[5,8,7],[6,3,6],[5,8,5]],
        [[3,7,3],[4,5,7],[5,2,5],[4,5,5]],
        [[2,8,3],[3,2,7],[1,2,6],[3,1,5]],
    ], dtype=numpy.float32
)

window_size = 2
sample_count = 3 * (my_input.shape[0] - window_size + 1) * (my_input.shape[1] - window_size + 1)
print('window_size -> ' + str(window_size) + ' ... sample_count -> ' + str(sample_count))
my_output = numpy.zeros((sample_count, window_size, window_size), dtype=numpy.float32)

_x = _convert.ffi.cast('size_t', my_input.shape[0])
_y = _convert.ffi.cast('size_t', my_input.shape[1])
_window_size = _convert.ffi.cast('size_t', window_size)
_my_input = _convert.ffi.cast('float *', my_input.ctypes.data)
_my_output = _convert.ffi.cast('float *', my_output.ctypes.data)

_convert.lib.sample3d(_x, _y, _window_size, _my_input, _my_output)

print(_my_output)

def float32_convert(output, img_data):
    _x = _convert.ffi.cast('size_t', output.shape[0])
    _y = _convert.ffi.cast('size_t', output.shape[1])
    _z = _convert.ffi.cast('size_t', output.shape[2])
    _output = _convert.ffi.cast('float *', output.ctypes.data)
    _convert.lib.float32_convert(_x, _y, _z, _output, img_data)

def calc_result(w,h,output):
    _shape = _convert.ffi.cast('size_t', output.shape[0])
    _w = _convert.ffi.cast('int', w)
    _h = _convert.ffi.cast('int', h)
    _output = _convert.ffi.cast('float *', output.ctypes.data)
    result = ffi.string(_convert.lib.calc_result(_w,_h,_shape,_output))
    print('{}'.format(result))
    return result
_convert.lib.init_darknet()
