#include <iostream>
#include <opencv2/opencv.hpp>
#include "utils.h"
#include "mtcnn.h"

void image_show(int argc, char* argv[]) {
    std::string imagepath = argv[1];
    cv::Mat cv_img = cv::imread(imagepath, CV_LOAD_IMAGE_COLOR);
    cv::namedWindow("face_detection", cv::WINDOW_NORMAL);
    std::cout << "cols: " << cv_img.cols << "\trows: " << cv_img.rows << std::endl;
    resizeWindow("face_detection", cv_img.cols/2, cv_img.rows/2);
    imshow("face_detection", cv_img);
    
    cv::waitKey(0);    
}

int main(int argc, char** argv)
{
    if(argc != 3) {
		std::cout << "usage: main $model_path $image_path" << std::endl;
		exit(1); 
	}
    std::string model_path = argv[1];
    std::string imagepath = argv[2];
    cv::Mat cv_img = cv::imread(imagepath, CV_LOAD_IMAGE_COLOR);
    if (cv_img.empty())
    {
        std::cerr << "cv::Imread failed. File Path: " << imagepath << std::endl;
        return -1;
    }
    std::vector<Bbox> finalBbox;
    MTCNN mm(model_path);

    // exit(0);
    ncnn::Mat ncnn_img = ncnn::Mat::from_pixels(cv_img.data, ncnn::Mat::PIXEL_BGR2RGB, cv_img.cols, cv_img.rows);
    struct timeval  tv1,tv2;
    struct timezone tz1,tz2;

    gettimeofday(&tv1,&tz1);
    mm.detect(ncnn_img, finalBbox);
    gettimeofday(&tv2,&tz2);
    int total = 0;
    for(vector<Bbox>::iterator it=finalBbox.begin(); it!=finalBbox.end();it++) {
    	if((*it).exist) {
            total++;
            cv::rectangle(cv_img, cv::Point((*it).x1, (*it).y1), cv::Point((*it).x2, (*it).y2), cv::Scalar(0,0,255), 2,8,0);
            for(int num=0;num<5;num++) {
                circle(cv_img, cv::Point((int)*(it->ppoint+num), (int)*(it->ppoint+num+5)), 3, cv::Scalar(0,255,255), -1);
            }
        }
    }
    std::cout << "detected " << total << " Persons. time eclipsed: " <<  getElapse(&tv1, &tv2) << " ms" << std::endl;
 
    cv::namedWindow("face_detection", cv::WINDOW_NORMAL);
    imshow("face_detection", cv_img);
    cv::waitKey(0);
    return 0;
}