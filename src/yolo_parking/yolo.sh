export LD_LIBRARY_PATH=$LD_LIBRARY:/system/vendor/lib:/system/vendor/lib/egl:$PREFIX/lib:/system/lib
export LD_PRELOAD=$LD_PRELOAD:libm.so:libpython2.7.so:libatomic.so:libcutils.so:/data/data/com.termux/files/home/sharpai/model/yolo/libdarknet.so

python2 yolo.py