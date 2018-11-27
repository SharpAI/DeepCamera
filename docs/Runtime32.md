

```
scp -P 8022 usr/lib/libatomic.so a@10.20.10.93:/data/data/com.termux/files/usr/lib
pkg install openjpeg
wget https://its-pointless.github.io/setup-pointless-repo.sh
$PREFIX/bin/wget https://its-pointless.github.io/setup-pointless-repo.sh
bash setup-pointless-repo.sh
pkg install libgfortran5
pkg install openblas
pkg install libffi libcompiler-rt ndk-sysroot libllvm redis mosquitto nodejs-lts

cd /data/data/com.termux/files/usr/lib
ln -s librt.so librt.so.1
```

Untar binary from prebuilt root fs
```
$ tar -cf libopencv2.tar libopencv_*
$ scp -P 8022 libopencv2.tar a@10.20.10.93:/data/data/com.termux/files/usr/lib/
$ scp -P 8022 libpython2.7.so.1.0 a@10.20.10.93:/data/data/com.termux/files/usr/lib/
```

```
cd /data/data/com.termux/files/usr/lib/
tar -xvf libopencv2.tar
ln -s libpython2.7.so.1.0 libpython2.7.so

rm /data/data/com.termux/files/usr/var/cache/apt/archives/*.deb
```
