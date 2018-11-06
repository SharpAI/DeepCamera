##  Build for Android
```
cd glfw
mkdir build && cd build
cmake ../ -DANDROID=ON -DGLFW_INCLUDE_ES1=ON -DGLFW_INCLUDE_ESEXT=ON -DGLFW_INCLUDE_NONE=ON -DBUILD_SHARED_LIBS=ON -DGLFW_BUILD_EXAMPLES=OFF -DGLFW_BUILD
_TESTS=OFF -DCMAKE_INSTALL_PREFIX=$PREFIX
make && make install
cd ..
```

```
cd opengl-test
mkdir build && cd build
cmake ..
make

LD_LIBRARY_PATH=/system/lib64:/system/vendor/lib64 ./opengl_test
```
