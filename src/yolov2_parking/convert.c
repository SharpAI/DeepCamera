
#include <stdlib.h> // import size_t
#include <string.h>
#include "darknet.h" // import darknet

//const char *voc_names[] = {"aeroplane", "bicycle", "bird", "boat", "bottle", "bus", "car", "cat", "chair", "cow", "diningtable", "dog", "horse", "motorbike", "person", "pottedplant", "sheep", "sofa", "train", "tvmonitor"};

const char *voc_names[] = {"person","bicycle","car","motorbike","aeroplane","bus","train","truck","boat","traffic_light","fire_hydrant","stop_sign","parking_meter","bench","bird","cat","dog","horse","sheep","cow","elephant","bear","zebra","giraffe","backpack","umbrella","handbag","tie","suitcase","frisbee","skis","snowboard","sports_ball","kite","baseball_bat","baseball_glove","skateboard","surfboard","tennis_racket","bottle","wine_glass","cup","fork","knife","spoon","bowl","banana","apple","sandwich","orange","broccoli","carrot","hot_dog","pizza","donut","cake","chair","sofa","pottedplant","bed","diningtable","toilet","tvmonitor","laptop","mouse","remote","keyboard","cell_phone","microwave","oven","toaster","sink","refrigerator","book","clock","vase","scissors","teddy_bear","hair_drier","toothbrush"};


char * print_detector_detections_old(char *id, box *boxes, float **probs, int total, int classes, int w, int h)
{
    int i, j;
    char tmp[20*2048];
    tmp[0] = 0;
    for(i = 0; i < total; ++i){
        float xmin = boxes[i].x - boxes[i].w/2. + 1;
        float xmax = boxes[i].x + boxes[i].w/2. + 1;
        float ymin = boxes[i].y - boxes[i].h/2. + 1;
        float ymax = boxes[i].y + boxes[i].h/2. + 1;

        if (xmin < 1) xmin = 1;
        if (ymin < 1) ymin = 1;
        if (xmax > w) xmax = w;
        if (ymax > h) ymax = h;

        for(j = 0; j < classes; ++j){
            if (probs[i][j]) sprintf(tmp,"%s %s %f %f %f %f %f\n",tmp, voc_names[j], probs[i][j],
                    xmin, ymin, xmax, ymax);
        }
    }
    return strdup(tmp);
}

char * print_detector_detections(char *id, box *boxes, float **probs, int total, int classes, int w, int h)
{
    int i, j;
    char tmp[20*2048];
    tmp[0] = 0;
    for(i = 0; i < total; ++i){
        float xmin = (boxes[i].x - boxes[i].w/2.)*w ;//+ 1;
        float xmax = (boxes[i].x + boxes[i].w/2.)*w ;//+ 1;
        float ymin = (boxes[i].y - boxes[i].h/2.)*h ;//+ 1;
        float ymax = (boxes[i].y + boxes[i].h/2.)*h ;//+ 1;

        if (xmin < 0) xmin = 0;
        if (ymin < 0) ymin = 0;
        if (xmax > w -1) xmax = w-1;
        if (ymax > h -1) ymax = h-1;

        for(j = 0; j < classes; ++j){
            if (probs[i][j]) sprintf(tmp,"%s %s %f %d %d %d %d\n",tmp, voc_names[j], probs[i][j],
                    (int)xmin, (int)ymin, (int)xmax, (int)ymax);
        }
    }
    return strdup(tmp);
}

void sample3d(size_t row_count, size_t column_count, size_t window_size, float *input, float *output) {
    printf("row count-> %zu \n", row_count);
    printf("col count -> %zu \n", column_count);
    printf("window size -> %zu \n", window_size);
    size_t i, j, k, a, b, output_offset, output_window_offset, output_idx = 0;
    for(i = 0; i < row_count - window_size + 1; i += 1) {
        for(j = 0; j < column_count - window_size + 1; j += 1) {
            for(k = 0; k < 3; k += 1) {
                //printf("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n");
                // generate window for current i,j position
                for(a = 0; a < window_size; a++) {
                    for(b = 0; b < window_size; b++) {
                        output_offset = window_size * window_size * output_idx;
                        output_window_offset = (window_size * a + b);
                        /*
                        printf("output offset -> %zu \n", output_offset);
                        printf("output window offset -> %zu \n", output_window_offset);
                        printf("output_idx -> %zu \n", output_idx);
                        
                        printf("\n"); 
                        printf("input[column_count * (i + a) + (j + b)] -> %2.2f \n", input[column_count * (i + a) + (j + b)]);
                        printf("i -> %zu \n", i);
                        printf("a -> %zu \n", a);
                        printf("j -> %zu \n", j);
                        printf("b -> %zu \n", b);
                        */
                        output[output_offset + output_window_offset + k] = input[column_count * (i + a) + (j + b) + k];
                    }
                }
            output_idx += 1;
            }
        }
    }
}
void float32_convert(size_t _c, size_t _h, size_t _w, float *output, float *data) {
    printf("c count-> %zu \n", _c);
    printf("h count -> %zu \n", _h);
    printf("w count -> %zu \n", _w);
    size_t c, h, k, i = 0;
    float *p=output;
    for(c = 0; c < _c; c++) {
        for(h = 0; h < _h ; h++) {
            for(k = 0; k < _w; k++) {
                *p = data[i];
		p++;
                i++;
            }
        }
    }
}

network *net;
layer l;
int classes;
float iou_thresh = .5;
float thresh = .24;
char* id;


void init_darknet(void){
    net = load_network("od.cfg", NULL, 0);
    id = basecfg("od.cfg");
    l = net->layers[net->n-1];
    classes = l.classes;
}

char * calc_result(int orig_w, int orig_h, size_t shape, float *output){
    int nboxes = 0;
    int j;
    int *map = 0;

    box *boxes = calloc(l.w*l.h*l.n, sizeof(box));
    float **probs = calloc(l.w*l.h*l.n, sizeof(float *));
    for(j = 0; j < l.w*l.h*l.n; ++j) probs[j] = calloc(l.classes + 1, sizeof(float *));
    float **masks = 0;
    if (l.coords > 4){
        masks = calloc(l.w*l.h*l.n, sizeof(float*));
        for(j = 0; j < l.w*l.h*l.n; ++j) masks[j] = calloc(l.coords-4, sizeof(float *));
    }

    for(int i = 0; i < shape; i++) {
        l.output[i] = output[i];
    }
    get_region_boxes(l, orig_w, orig_h, net->w, net->h, thresh, probs, boxes, 0, 0, map, .5, 1);
    
    do_nms_sort(boxes, probs, l.w*l.h*l.n, l.classes, 0.3);
    char * result = print_detector_detections(id, boxes, probs, l.w*l.h*l.n, classes, orig_w, orig_h);

    free(boxes);
    free_ptrs((void **)probs, l.w*l.h*l.n);
    return result;
}
