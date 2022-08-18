import os
import ctypes

from PyInstaller.utils.hooks import logger, get_package_paths,collect_data_files
from PyInstaller.depend.utils import _resolveCtypesImports

binaries = []
pkg_base, pkg_dir = get_package_paths('flower')

binaries += [(os.path.join(pkg_dir, 'static'),'flower/static')]
binaries += [(os.path.join(pkg_dir, 'templates'),'flower/templates')]
binaries += [(os.path.join(pkg_dir, 'views'),'flower/views')]

logger.warning(binaries)
#logger.warning(datas)
