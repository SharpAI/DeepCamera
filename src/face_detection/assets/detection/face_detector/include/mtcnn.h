#ifndef __MTCNN_H__
#define __MTCNN_H__

#include <vector>
#include "net.h"

using namespace std;
using namespace cv;

struct Bbox
{
    float score;
    int x1;
    int y1;
    int x2;
    int y2;
    float area;
    bool exist;
    float ppoint[10];
    float regreCoord[4];
};

struct orderScore
{
    float score;
    int oriOrder;
};


class MTCNN{
public:
    MTCNN();
    MTCNN(const std::string& model_path);
    void detect(ncnn::Mat& img_, std::vector<Bbox>& finalBbox);
    void setMinSize(int min);
    void setThreshold(float t1,float t2,float t3);
    void setNumThreads(int num_thread);

private:
    void generateBbox(ncnn::Mat score, ncnn::Mat location, vector<Bbox>& boundingBox_, vector<orderScore>& bboxScore_, float scale);
    void nms(vector<Bbox> &boundingBox_, std::vector<orderScore> &bboxScore_, const float overlap_threshold, string modelname="Union");
    void refineAndSquareBbox(vector<Bbox> &vecBbox, const int &height, const int &width);

    ncnn::Net pnet_, rnet_, onet_;
    ncnn::Mat img;

    const float nms_threshold[3] = {0.5, 0.7, 0.7};
    const float mean_vals[3] = {127.5, 127.5, 127.5};
    const float norm_vals[3] = {0.0078125, 0.0078125, 0.0078125};
    float threshold[3] = {0.7, 0.6, 0.7};
    int min_size = 40;
    int num_threads = 1;
    std::vector<Bbox> firstBbox_, secondBbox_,thirdBbox_;
    
    std::vector<orderScore> firstOrderScore_, secondBboxScore_, thirdBboxScore_;
    int img_w, img_h;
};


#endif
