import os
import ctypes

from PyInstaller.utils.hooks import collect_dynamic_libs, logger, get_package_paths
from PyInstaller.depend.utils import _resolveCtypesImports

def collect_native_files(package, files):
    pkg_base, pkg_dir = get_package_paths(package)
    return [(os.path.join(pkg_dir, file), '.') for file in files]

#files = ['libGLES_mali.so']
excludes = ['tvm._ffi._cy3.core','tvm._ffi._cy3']

#datas = collect_native_files('tvm', files)

binaries = collect_dynamic_libs("tvm")
binaries += _resolveCtypesImports('libtvm')
hiddenimports = ['_cffi_backend','tvm._ffi._ctypes',
        'tvm._ffi._ctypes.ndarray','tvm._ffi._cy2','tvm._ffi._cy2.core']
logger.warning(binaries)
#logger.warning(datas)
