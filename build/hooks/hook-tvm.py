from PyInstaller.utils.hooks import collect_dynamic_libs

binaries = collect_dynamic_libs("tvm")
binaries += collect_dynamic_libs("tvm-runtime")
