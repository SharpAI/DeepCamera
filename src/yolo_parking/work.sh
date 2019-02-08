export LD_LIBRARY_PATH=$LD_LIBRARY:/system/vendor/lib:/system/vendor/lib/egl:$PREFIX/lib:/system/lib
export LD_PRELOAD=libatomic.so:libcutils.so

python2 work.py worker --loglevel INFO -E -n detect -c 1 -Q detect