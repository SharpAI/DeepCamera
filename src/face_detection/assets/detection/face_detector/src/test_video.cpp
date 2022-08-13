#include <iostream>
#include <opencv2/opencv.hpp>
#include "utils.h"
#include "mtcnn.h"

#define QUIT_KEY 'q'

void test_video(int argc, char* argv[]) {
	if(argc != 3) {
		std::cout << "usage: test_video $model_path $camera_id" << std::endl;
		exit(1); 
	}

	std::string model_path = argv[1];
	int camera_id = atoi(argv[2]);
	MTCNN mm(model_path);

    cv::VideoCapture camera(camera_id);

    if (!camera.isOpened()) {
        std::cerr << "failed to open camera" << std::endl;
        return;
    }

	std::vector<Bbox> finalBbox;
	cv::Mat frame;
	clock_t start_time = clock();

   	do {
		finalBbox.clear();
        camera >> frame;
        if (!frame.data) {
            std::cerr << "Capture video failed" << std::endl;
            break;
        }

		ncnn::Mat ncnn_img = ncnn::Mat::from_pixels(frame.data, ncnn::Mat::PIXEL_BGR2RGB, frame.cols, frame.rows);
		mm.detect(ncnn_img, finalBbox);

    	for(vector<Bbox>::iterator it=finalBbox.begin(); it!=finalBbox.end();it++) {
    		if((*it).exist) {
            	cv::rectangle(frame, cv::Point((*it).x1, (*it).y1), cv::Point((*it).x2, (*it).y2), cv::Scalar(0,0,255), 2,8,0);
            	for(int num=0;num<5;num++) {
                	circle(frame, cv::Point((int)*(it->ppoint+num), (int)*(it->ppoint+num+5)), 3, cv::Scalar(0,255,255), -1);
            	}
        	}
    	}

		imshow("face_detection", frame);

    } while (QUIT_KEY != cv::waitKey(100));

	clock_t finish_time = clock();
	double total_time = (double)(finish_time - start_time) / CLOCKS_PER_SEC;
	std::cout << "time: " << total_time * 1000 << "ms" << std::endl;
}

int main(int argc, char* argv[]) {
    test_video(argc, argv);
}