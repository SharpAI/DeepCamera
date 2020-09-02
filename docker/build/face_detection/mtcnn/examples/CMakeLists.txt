
set(OpenCV_Install /Users/hongtaozhang/workspace/machine-learning/face_detect/opencv-master/install_loc)
set(OpenCV_DIR ${OpenCV_Install}/share/OpenCV)

#find_package(OpenCV QUIET COMPONENTS core highgui imgproc imgcodecs)
#if(NOT OpenCV_FOUND)
#    find_package(OpenCV REQUIRED COMPONENTS core highgui imgproc)
#endif()

find_package(OpenCV REQUIRED)

if (NOT OpenCV_FOUND)
    message(FATAL_ERROR "opencv Not Found!")
else()
    message(STATUS "OpenCV_LIBS: ${OpenCV_LIBS}")
    message(STATUS "OpenCV_INCLUDE_DIRS: ${OpenCV_INCLUDE_DIRS}")
endif (NOT OpenCV_FOUND)

include_directories(${OpenCV_INCLUDE_DIRS})
include_directories(${CMAKE_CURRENT_SOURCE_DIR}/../src)
include_directories(${CMAKE_CURRENT_BINARY_DIR}/../src)

add_executable(squeezenet squeezenet.cpp)
target_link_libraries(squeezenet ncnn ${OpenCV_LIBS})

add_executable(fasterrcnn fasterrcnn.cpp)
target_link_libraries(fasterrcnn ncnn ${OpenCV_LIBS})

add_subdirectory(ssd)
