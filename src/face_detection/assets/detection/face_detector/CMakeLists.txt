cmake_minimum_required(VERSION 2.8.10)

project(mtcnn_ncnn)
add_subdirectory(pybind11)
if(NOT CMAKE_BUILD_TYPE)
    message(STATUS "build type not defined")
    set(CMAKE_BUILD_TYPE release CACHE STRING "Choose the type of build" FORCE)
endif()

if(CMAKE_BUILD_TYPE STREQUAL debug)
    message(STATUS "debug mode")
    ADD_DEFINITIONS(-D__DEBUG__)
else()
    message(STATUS "release mode")
ENDIF()

SET(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -std=c++11")

find_package(OpenMP)
if(OpenMP_CXX_FOUND OR OPENMP_FOUND)
    set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} ${OpenMP_C_FLAGS}")
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} ${OpenMP_CXX_FLAGS}")
endif()

find_package( OpenCV REQUIRED )

if (NOT OpenCV_FOUND)
    message(FATAL_ERROR "opencv Not Found!")
else()
    message(STATUS "OpenCV_LIBS: ${OpenCV_LIBS}")
    message(STATUS "OpenCV_INCLUDE_DIRS: ${OpenCV_INCLUDE_DIRS}")
endif (NOT OpenCV_FOUND)

message(STATUS "CMAKE_CURRENT_SOURCE_DIR: ${CMAKE_CURRENT_SOURCE_DIR}")
message(STATUS "CMAKE_CURRENT_BINARY_DIR: ${CMAKE_CURRENT_BINARY_DIR}")
include_directories(${OpenCV_INCLUDE_DIRS})
include_directories(${PROJECT_SOURCE_DIR}/include)
include_directories(${PROJECT_SOURCE_DIR}/include/ncnn)


link_directories(
  ${OpenCV_Install}/lib
  ${PROJECT_SOURCE_DIR}/lib/ncnn
)

add_executable(main src/main.cpp src/utils.cpp src/mtcnn.cpp)
target_link_libraries(main ncnn ${OpenCV_LIBS})
set_target_properties(main
        PROPERTIES
#        ARCHIVE_OUTPUT_DIRECTORY "${PROJECT_SOURCE_DIR}/lib"
#        LIBRARY_OUTPUT_DIRECTORY "${PROJECT_SOURCE_DIR}/lib"
        RUNTIME_OUTPUT_DIRECTORY "${PROJECT_SOURCE_DIR}/bin"
)

pybind11_add_module(face_detection src/py_face_detection.cpp src/utils.cpp src/mtcnn.cpp)
target_link_libraries(face_detection PRIVATE ncnn ${OpenCV_LIBS})
#set_target_properties(face_detection
#        PROPERTIES
#        ARCHIVE_OUTPUT_DIRECTORY "${PROJECT_SOURCE_DIR}/lib"
#        LIBRARY_OUTPUT_DIRECTORY "${PROJECT_SOURCE_DIR}/lib"
#        RUNTIME_OUTPUT_DIRECTORY "${PROJECT_SOURCE_DIR}/bin"
#)

add_executable(benchmark src/benchmark.cpp src/utils.cpp src/mtcnn.cpp)
target_link_libraries(benchmark ncnn ${OpenCV_LIBS})
set_target_properties(benchmark
        PROPERTIES
#        ARCHIVE_OUTPUT_DIRECTORY "${PROJECT_SOURCE_DIR}/lib"
#        LIBRARY_OUTPUT_DIRECTORY "${PROJECT_SOURCE_DIR}/lib"
        RUNTIME_OUTPUT_DIRECTORY "${PROJECT_SOURCE_DIR}/bin"
)

add_executable(test_picture src/test_picture.cpp src/utils.cpp src/mtcnn.cpp)
target_link_libraries(test_picture ncnn ${OpenCV_LIBS})
set_target_properties(test_picture
        PROPERTIES
#        ARCHIVE_OUTPUT_DIRECTORY "${PROJECT_SOURCE_DIR}/lib"
#        LIBRARY_OUTPUT_DIRECTORY "${PROJECT_SOURCE_DIR}/lib"
        RUNTIME_OUTPUT_DIRECTORY "${PROJECT_SOURCE_DIR}/bin"
)

add_executable(test_video src/test_video.cpp src/utils.cpp src/mtcnn.cpp)
target_link_libraries(test_video ncnn ${OpenCV_LIBS})
set_target_properties(test_video
        PROPERTIES
#        ARCHIVE_OUTPUT_DIRECTORY "${PROJECT_SOURCE_DIR}/lib"
#        LIBRARY_OUTPUT_DIRECTORY "${PROJECT_SOURCE_DIR}/lib"
        RUNTIME_OUTPUT_DIRECTORY "${PROJECT_SOURCE_DIR}/bin"
)
