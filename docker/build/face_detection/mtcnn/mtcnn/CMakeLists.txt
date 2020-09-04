#set(OpenCV_Install /Users/hongtaozhang/workspace/machine-learning/face_detect/opencv-master/install_loc)
#set(OpenCV_DIR ${OpenCV_Install}/share/OpenCV)

find_package( OpenCV REQUIRED )
#find_package(OpenCV REQUIRED core highgui imgproc)

if (NOT OpenCV_FOUND)
    message(FATAL_ERROR "opencv Not Found!")
else()
    message(STATUS "OpenCV_LIBS: ${OpenCV_LIBS}")
    message(STATUS "OpenCV_INCLUDE_DIRS: ${OpenCV_INCLUDE_DIRS}")
endif (NOT OpenCV_FOUND)

message(STATUS "CMAKE_CURRENT_SOURCE_DIR: ${CMAKE_CURRENT_SOURCE_DIR}")
message(STATUS "CMAKE_CURRENT_SOURCE_DIR: ${CMAKE_CURRENT_BINARY_DIR}")
include_directories(${OpenCV_INCLUDE_DIRS})
include_directories(${CMAKE_CURRENT_SOURCE_DIR})
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/../src)
include_directories(${CMAKE_CURRENT_BINARY_DIR}/../src)

link_directories(
  ${OpenCV_Install}/lib
)
add_executable(mtcnn mtcnn.cpp)

target_link_libraries(mtcnn ncnn ${OpenCV_LIBS})
