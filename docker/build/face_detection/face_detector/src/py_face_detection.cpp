#include <iostream>
#include <string>

#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include <opencv2/opencv.hpp>
#include "utils.h"
#include "mtcnn.h"

MTCNN *mm;

void loop_test(std::string folder_path) {
    std::vector<string> file_list;
    trave_dir(folder_path, file_list);
    std::cout << "file num: " << file_list.size() << std::endl;

    std::vector<Bbox> finalBbox;
    int detected = 0;
    struct timeval  tv1,tv2;
    struct timezone tz1,tz2;
    float min, max, total = 0;
    for(int i = 0; i < 10; i++){
        for(std::vector<string>::iterator it=file_list.begin(); it != file_list.end(); it++) {
            cv::Mat cv_img = cv::imread(*it, CV_LOAD_IMAGE_COLOR);
            if (cv_img.empty()) {
                std::cerr << "cv::Imread failed. File Path: " << *it << std::endl;
                return;
            }
            finalBbox.clear();
            int face_num = 0;

            // exit(0);
            ncnn::Mat ncnn_img = ncnn::Mat::from_pixels(cv_img.data, ncnn::Mat::PIXEL_BGR2RGB, cv_img.cols, cv_img.rows);
            gettimeofday(&tv1, nullptr);
            mm->detect(ncnn_img, finalBbox);
            gettimeofday(&tv2, nullptr);
            for(vector<Bbox>::iterator it=finalBbox.begin(); it!=finalBbox.end();it++){
                if((*it).exist){
                    face_num++;
                    // cv::rectangle(cv_img, Point((*it).x1, (*it).y1), Point((*it).x2, (*it).y2), Scalar(0,0,255), 2,8,0);
                    // for(int num=0;num<5;num++)circle(cv_img,Point((int)*(it->ppoint+num), (int)*(it->ppoint+num+5)),3,Scalar(0,255,255), -1);
                }
            }

            if(face_num > 0) {
                detected++;
                std::cout << "image path: " << *it << "\tface_num: " << face_num << std::endl;
            } else {
                std::cout << "image path: " << *it << "\tno faces found"<< std::endl;
            }

            float tc = getElapse(&tv1, &tv2);
            total += tc;
            if(min == 0 || min > tc){
                min = tc;
            }

            if(max == 0 || max < tc){
                max = tc;
            }
        }
    }

    float avg = total / file_list.size() / 10;
    std::cout << "warming up total images: " << file_list.size()*10 << "\tdetected " << detected
    << "\tmin time: " <<  min << "\tmax: " << max << "\tavg: " << avg << "\tms" << std::endl;

    for(int i = 0; i < 1000; i++){
        for(std::vector<string>::iterator it=file_list.begin(); it != file_list.end(); it++) {
            cv::Mat cv_img = cv::imread(*it, CV_LOAD_IMAGE_COLOR);
            if (cv_img.empty()) {
                std::cerr << "cv::Imread failed. File Path: " << *it << std::endl;
                return;
            }
            finalBbox.clear();
            int face_num = 0;

            // exit(0);
            ncnn::Mat ncnn_img = ncnn::Mat::from_pixels(cv_img.data, ncnn::Mat::PIXEL_BGR2RGB, cv_img.cols, cv_img.rows);
            gettimeofday(&tv1, nullptr);
            mm->detect(ncnn_img, finalBbox);
            gettimeofday(&tv2, nullptr);
            for(vector<Bbox>::iterator it=finalBbox.begin(); it!=finalBbox.end();it++){
                if((*it).exist){
                    face_num++;
                    // cv::rectangle(cv_img, Point((*it).x1, (*it).y1), Point((*it).x2, (*it).y2), Scalar(0,0,255), 2,8,0);
                    // for(int num=0;num<5;num++)circle(cv_img,Point((int)*(it->ppoint+num), (int)*(it->ppoint+num+5)),3,Scalar(0,255,255), -1);
                }
            }

            if(face_num > 0) {
                detected++;
                std::cout << "image path: " << *it << "\tface_num: " << face_num << std::endl;
            } else {
                std::cout << "image path: " << *it << "\tno faces found"<< std::endl;
            }

            float tc = getElapse(&tv1, &tv2);
            total += tc;
            if(min == 0 || min > tc){
                min = tc;
            }

            if(max == 0 || max < tc){
                max = tc;
            }
        }
    }

    avg = total / file_list.size() / 1000;
    std::cout << "total images: " << file_list.size()*1000 << "\tdetected " << detected
    << "\tmin time: " <<  min << "\tmax: " << max << "\tavg: " << avg << "\tms" << std::endl;
}
void init(std::string model_path){
  mm=new MTCNN(model_path);
}
void set_minsize(int min_size){
  mm->setMinSize(min_size);
}
void set_threshold(float f1,float f2,float f3){
  mm->setThreshold(f1,f2,f3);
}
void set_num_threads(int num_threads){
  mm->setNumThreads(num_threads);
}
std::string detect(std::string imagepath) {
    struct timeval  tv1,tv2;
    struct timezone tz1,tz2;
    std::vector<Bbox> finalBbox;
    int detected = 0;
    cv::Mat cv_img = cv::imread(imagepath, CV_LOAD_IMAGE_COLOR);
    if (cv_img.empty()) {
        std::cerr << "cv::Imread failed. File Path: " << imagepath << std::endl;
        return "{\"result\":[]}";
    }
    finalBbox.clear();
    int face_num = 0;

    ncnn::Mat ncnn_img = ncnn::Mat::from_pixels(cv_img.data, ncnn::Mat::PIXEL_BGR2RGB, cv_img.cols, cv_img.rows);

    gettimeofday(&tv1,&tz1);
    mm->detect(ncnn_img, finalBbox);
    gettimeofday(&tv2,&tz2);

    std::ostringstream result;
    result << "{\"result\":[";
    for(vector<Bbox>::iterator it=finalBbox.begin(); it!=finalBbox.end();it++){
        if((*it).exist){
            // cv::rectangle(cv_img, Point((*it).x1, (*it).y1), Point((*it).x2, (*it).y2), Scalar(0,0,255), 2,8,0);
            // for(int num=0;num<5;num++)circle(cv_img,Point((int)*(it->ppoint+num), (int)*(it->ppoint+num+5)),3,Scalar(0,255,255), -1);

            if (face_num != 0){
              result << ",";
            }
            face_num++;

            result <<   "{ \"score\" :" << (*it).score << ",";
            result <<   "   \"bbox\"  : [" << (*it).x1 << "," << (*it).y1 << "," <<(*it).x2 <<","<<(*it).y2<<"],";
            result <<   "   \"landmark\":[ ";
            result <<   "        [" << (int)*(it->ppoint+0) << "," << (int)*(it->ppoint+0+5) << "] ,";
            result <<   "        [" << (int)*(it->ppoint+1) << "," << (int)*(it->ppoint+1+5) << "] ,";
            result <<   "        [" << (int)*(it->ppoint+2) << "," << (int)*(it->ppoint+2+5) << "] ,";
            result <<   "        [" << (int)*(it->ppoint+3) << "," << (int)*(it->ppoint+3+5) << "] ,";
            result <<   "        [" << (int)*(it->ppoint+4) << "," << (int)*(it->ppoint+4+5) << "]";
            result <<   "   ]";
            result <<   "}"; // score
        }
    }
    result << "]}";
    #ifdef __DEBUG__
    printf( "%s = %g ms \n ", "Detection time", getElapse(&tv1, &tv2) );
    #endif
    ncnn_img.release();
    cv_img.release();
    return result.str();
}
PYBIND11_MODULE(face_detection, m) {
    m.doc() = R"pbdoc(
        Pybind11 example plugin
        -----------------------

        .. currentmodule:: face_detection

        .. autosummary::
           :toctree: _generate

           detect
    )pbdoc";

    m.def("loop_test", &loop_test, R"pbdoc(
        loop test function
    )pbdoc");

    m.def("detect", &detect, R"pbdoc(
        detect function
    )pbdoc");

    m.def("set_minsize", &set_minsize, R"pbdoc(
        set min size function
    )pbdoc");

    m.def("set_threshold", &set_threshold, R"pbdoc(
        set threshold function
    )pbdoc");

    m.def("set_num_threads", &set_num_threads, R"pbdoc(
        set threshold function
    )pbdoc");

    m.def("init", &init, R"pbdoc(
        init model
    )pbdoc");
#ifdef VERSION_INFO
    m.attr("__version__") = VERSION_INFO;
#else
    m.attr("__version__") = "dev";
#endif
}
