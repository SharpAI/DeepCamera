#include <iostream>
#include <string>
#include <opencv2/opencv.hpp>
#include "utils.h"
#include "mtcnn.h"

void benchmark(int argc, char** argv) {
    if(argc != 3) {
		std::cout << "usage: benchmark $model_path $image_folder" << std::endl;
		exit(1); 
	}
    std::string model_path = argv[1];
    std::string folder_path = argv[2];
    std::vector<string> file_list;
    trave_dir(folder_path, file_list);
    std::cout << "file num: " << file_list.size() << std::endl;

    std::vector<Bbox> finalBbox;
    MTCNN mm(model_path);
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
        mm.detect(ncnn_img, finalBbox);
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
        mm.detect(ncnn_img, finalBbox);
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

// std::string model_path = argv[1];
// std::string folder_path = argv[2];
int main(int argc, char** argv)
{
    benchmark(argc, argv);
}
