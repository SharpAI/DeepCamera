/*
 * yolo_layer.cu
 *
 * This code was originally written by wang-xinyu under MIT license.
 * I took it from:
 *
 *     https://github.com/wang-xinyu/tensorrtx/tree/master/yolov4
 *
 * and made necessary modifications.
 *
 * - JK Jung
 */

#include "yolo_layer.h"

using namespace Yolo;

namespace
{
// Write values into buffer
template <typename T>
void write(char*& buffer, const T& val)
{
    *reinterpret_cast<T*>(buffer) = val;
    buffer += sizeof(T);
}

// Read values from buffer
template <typename T>
void read(const char*& buffer, T& val)
{
    val = *reinterpret_cast<const T*>(buffer);
    buffer += sizeof(T);
}
} // namespace

namespace nvinfer1
{
    YoloLayerPlugin::YoloLayerPlugin(int yolo_width, int yolo_height, int num_anchors, float* anchors, int num_classes, int input_width, int input_height, float scale_x_y, int new_coords)
    {
        mYoloWidth   = yolo_width;
        mYoloHeight  = yolo_height;
        mNumAnchors  = num_anchors;
        memcpy(mAnchorsHost, anchors, num_anchors * 2 * sizeof(float));
        mNumClasses  = num_classes;
        mInputWidth  = input_width;
        mInputHeight = input_height;
        mScaleXY     = scale_x_y;
        mNewCoords   = new_coords;

        CHECK(cudaMalloc(&mAnchors, MAX_ANCHORS * 2 * sizeof(float)));
        CHECK(cudaMemcpy(mAnchors, mAnchorsHost, mNumAnchors * 2 * sizeof(float), cudaMemcpyHostToDevice));
    }

    YoloLayerPlugin::YoloLayerPlugin(const void* data, size_t length)
    {
        const char *d = reinterpret_cast<const char *>(data), *a = d;
        read(d, mThreadCount);
        read(d, mYoloWidth);
        read(d, mYoloHeight);
        read(d, mNumAnchors);
        memcpy(mAnchorsHost, d, MAX_ANCHORS * 2 * sizeof(float));
        d += MAX_ANCHORS * 2 * sizeof(float);
        read(d, mNumClasses);
        read(d, mInputWidth);
        read(d, mInputHeight);
        read(d, mScaleXY);
        read(d, mNewCoords);

        CHECK(cudaMalloc(&mAnchors, MAX_ANCHORS * 2 * sizeof(float)));
        CHECK(cudaMemcpy(mAnchors, mAnchorsHost, mNumAnchors * 2 * sizeof(float), cudaMemcpyHostToDevice));

        assert(d == a + length);
    }

    void YoloLayerPlugin::serialize(void* buffer) const
    {
        char* d = static_cast<char*>(buffer), *a = d;
        write(d, mThreadCount);
        write(d, mYoloWidth);
        write(d, mYoloHeight);
        write(d, mNumAnchors);
        memcpy(d, mAnchorsHost, MAX_ANCHORS * 2 * sizeof(float));
        d += MAX_ANCHORS * 2 * sizeof(float);
        write(d, mNumClasses);
        write(d, mInputWidth);
        write(d, mInputHeight);
        write(d, mScaleXY);
        write(d, mNewCoords);

        assert(d == a + getSerializationSize());
    }

    size_t YoloLayerPlugin::getSerializationSize() const
    {
        return sizeof(mThreadCount) + \
               sizeof(mYoloWidth) + sizeof(mYoloHeight) + \
               sizeof(mNumAnchors) + MAX_ANCHORS * 2 * sizeof(float) + \
               sizeof(mNumClasses) + \
               sizeof(mInputWidth) + sizeof(mInputHeight) + \
               sizeof(mScaleXY) + sizeof(mNewCoords);
    }

    int YoloLayerPlugin::initialize()
    {
        return 0;
    }

    void YoloLayerPlugin::terminate()
    {
        CHECK(cudaFree(mAnchors));
    }

    Dims YoloLayerPlugin::getOutputDimensions(int index, const Dims* inputs, int nbInputDims)
    {
        assert(index == 0);
        assert(nbInputDims == 1);
        assert(inputs[0].d[0] == (mNumClasses + 5) * mNumAnchors);
        assert(inputs[0].d[1] == mYoloHeight);
        assert(inputs[0].d[2] == mYoloWidth);
        // output detection results to the channel dimension
        int totalsize = mYoloWidth * mYoloHeight * mNumAnchors * sizeof(Detection) / sizeof(float);
        return Dims3(totalsize, 1, 1);
    }

    void YoloLayerPlugin::setPluginNamespace(const char* pluginNamespace)
    {
        mPluginNamespace = pluginNamespace;
    }

    const char* YoloLayerPlugin::getPluginNamespace() const
    {
        return mPluginNamespace;
    }

    // Return the DataType of the plugin output at the requested index
    DataType YoloLayerPlugin::getOutputDataType(int index, const DataType* inputTypes, int nbInputs) const
    {
        return DataType::kFLOAT;
    }

    // Return true if output tensor is broadcast across a batch.
    bool YoloLayerPlugin::isOutputBroadcastAcrossBatch(int outputIndex, const bool* inputIsBroadcasted, int nbInputs) const
    {
        return false;
    }

    // Return true if plugin can use input that is broadcast across batch without replication.
    bool YoloLayerPlugin::canBroadcastInputAcrossBatch(int inputIndex) const
    {
        return false;
    }

    void YoloLayerPlugin::configurePlugin(const PluginTensorDesc* in, int nbInput, const PluginTensorDesc* out, int nbOutput)
    {
    }

    // Attach the plugin object to an execution context and grant the plugin the access to some context resource.
    void YoloLayerPlugin::attachToContext(cudnnContext* cudnnContext, cublasContext* cublasContext, IGpuAllocator* gpuAllocator)
    {
    }

    // Detach the plugin object from its execution context.
    void YoloLayerPlugin::detachFromContext()
    {
    }

    const char* YoloLayerPlugin::getPluginType() const
    {
        return "YoloLayer_TRT";
    }

    const char* YoloLayerPlugin::getPluginVersion() const
    {
        return "1";
    }

    void YoloLayerPlugin::destroy()
    {
        delete this;
    }

    // Clone the plugin
    IPluginV2IOExt* YoloLayerPlugin::clone() const
    {
        YoloLayerPlugin *p = new YoloLayerPlugin(mYoloWidth, mYoloHeight, mNumAnchors, (float*) mAnchorsHost, mNumClasses, mInputWidth, mInputHeight, mScaleXY, mNewCoords);
        p->setPluginNamespace(mPluginNamespace);
        return p;
    }

    inline __device__ float sigmoidGPU(float x) { return 1.0f / (1.0f + __expf(-x)); }

    inline __device__ float scale_sigmoidGPU(float x, float s)
    {
        return s * sigmoidGPU(x) - (s - 1.0f) * 0.5f;
    }

    // CalDetection(): This kernel processes 1 yolo layer calculation.  It
    // distributes calculations so that 1 GPU thread would be responsible
    // for each grid/anchor combination.
    // NOTE: The output (x, y, w, h) are between 0.0 and 1.0
    //       (relative to orginal image width and height).
    __global__ void CalDetection(const float *input, float *output,
                                 int batch_size,
                                 int yolo_width, int yolo_height,
                                 int num_anchors, const float *anchors,
                                 int num_classes, int input_w, int input_h,
                                 float scale_x_y)
    {
        int idx = threadIdx.x + blockDim.x * blockIdx.x;
        Detection* det = ((Detection*) output) + idx;
        int total_grids = yolo_width * yolo_height;
        if (idx >= batch_size * total_grids * num_anchors) return;

        int info_len = 5 + num_classes;
        //int batch_idx = idx / (total_grids * num_anchors);
        int group_idx = idx / total_grids;
        int anchor_idx = group_idx % num_anchors;
        const float* cur_input = input + group_idx * (info_len * total_grids) + (idx % total_grids);

        int class_id;
        float max_cls_logit = -CUDART_INF_F;  // minus infinity
        for (int i = 5; i < info_len; ++i) {
            float l = *(cur_input + i * total_grids);
            if (l > max_cls_logit) {
                max_cls_logit = l;
                class_id = i - 5;
            }
        }
        float max_cls_prob = sigmoidGPU(max_cls_logit);
        float box_prob = sigmoidGPU(*(cur_input + 4 * total_grids));
        //if (max_cls_prob < IGNORE_THRESH || box_prob < IGNORE_THRESH)
        //    return;

        int row = (idx % total_grids) / yolo_width;
        int col = (idx % total_grids) % yolo_width;

        det->bbox[0] = (col + scale_sigmoidGPU(*(cur_input + 0 * total_grids), scale_x_y)) / yolo_width;    // [0, 1]
        det->bbox[1] = (row + scale_sigmoidGPU(*(cur_input + 1 * total_grids), scale_x_y)) / yolo_height;   // [0, 1]
        det->bbox[2] = __expf(*(cur_input + 2 * total_grids)) * *(anchors + 2 * anchor_idx + 0) / input_w;  // [0, 1]
        det->bbox[3] = __expf(*(cur_input + 3 * total_grids)) * *(anchors + 2 * anchor_idx + 1) / input_h;  // [0, 1]

        det->bbox[0] -= det->bbox[2] / 2;  // shift from center to top-left
        det->bbox[1] -= det->bbox[3] / 2;

        det->det_confidence = box_prob;
        det->class_id = class_id;
        det->class_confidence = max_cls_prob;
    }

    inline __device__ float scale(float x, float s)
    {
        return s * x - (s - 1.0f) * 0.5f;
    }

    inline __device__ float square(float x)
    {
        return x * x;
    }

    __global__ void CalDetection_NewCoords(const float *input, float *output,
                                           int batch_size,
                                           int yolo_width, int yolo_height,
                                           int num_anchors, const float *anchors,
                                           int num_classes, int input_w, int input_h,
                                           float scale_x_y)
    {
        int idx = threadIdx.x + blockDim.x * blockIdx.x;
        Detection* det = ((Detection*) output) + idx;
        int total_grids = yolo_width * yolo_height;
        if (idx >= batch_size * total_grids * num_anchors) return;

        int info_len = 5 + num_classes;
        //int batch_idx = idx / (total_grids * num_anchors);
        int group_idx = idx / total_grids;
        int anchor_idx = group_idx % num_anchors;
        const float* cur_input = input + group_idx * (info_len * total_grids) + (idx % total_grids);

        int class_id;
        float max_cls_prob = -CUDART_INF_F;  // minus infinity
        for (int i = 5; i < info_len; ++i) {
            float l = *(cur_input + i * total_grids);
            if (l > max_cls_prob) {
                max_cls_prob = l;
                class_id = i - 5;
            }
        }
        float box_prob = *(cur_input + 4 * total_grids);
        //if (max_cls_prob < IGNORE_THRESH || box_prob < IGNORE_THRESH)
        //    return;

        int row = (idx % total_grids) / yolo_width;
        int col = (idx % total_grids) % yolo_width;

        det->bbox[0] = (col + scale(*(cur_input + 0 * total_grids), scale_x_y)) / yolo_width;                   // [0, 1]
        det->bbox[1] = (row + scale(*(cur_input + 1 * total_grids), scale_x_y)) / yolo_height;                  // [0, 1]
        det->bbox[2] = square(*(cur_input + 2 * total_grids)) * 4 * *(anchors + 2 * anchor_idx + 0) / input_w;  // [0, 1]
        det->bbox[3] = square(*(cur_input + 3 * total_grids)) * 4 * *(anchors + 2 * anchor_idx + 1) / input_h;  // [0, 1]

        det->bbox[0] -= det->bbox[2] / 2;  // shift from center to top-left
        det->bbox[1] -= det->bbox[3] / 2;

        det->det_confidence = box_prob;
        det->class_id = class_id;
        det->class_confidence = max_cls_prob;
    }

    void YoloLayerPlugin::forwardGpu(const float* const* inputs, float* output, cudaStream_t stream, int batchSize)
    {
        int num_elements = batchSize * mNumAnchors * mYoloWidth * mYoloHeight;

        //CHECK(cudaMemset(output, 0, num_elements * sizeof(Detection)));

        if (mNewCoords) {
            CalDetection_NewCoords<<<(num_elements + mThreadCount - 1) / mThreadCount, mThreadCount, 0, stream>>>
                (inputs[0], output, batchSize, mYoloWidth, mYoloHeight, mNumAnchors, (const float*) mAnchors, mNumClasses, mInputWidth, mInputHeight, mScaleXY);
        } else {
            CalDetection<<<(num_elements + mThreadCount - 1) / mThreadCount, mThreadCount, 0, stream>>>
                (inputs[0], output, batchSize, mYoloWidth, mYoloHeight, mNumAnchors, (const float*) mAnchors, mNumClasses, mInputWidth, mInputHeight, mScaleXY);
        }
    }

    int YoloLayerPlugin::enqueue(int batchSize, const void* const* inputs, void** outputs, void* workspace, cudaStream_t stream)
    {
        forwardGpu((const float* const*)inputs, (float*)outputs[0], stream, batchSize);
        return 0;
    }

    YoloPluginCreator::YoloPluginCreator()
    {
        mPluginAttributes.clear();

        mFC.nbFields = mPluginAttributes.size();
        mFC.fields = mPluginAttributes.data();
    }

    const char* YoloPluginCreator::getPluginName() const
    {
        return "YoloLayer_TRT";
    }

    const char* YoloPluginCreator::getPluginVersion() const
    {
        return "1";
    }

    const PluginFieldCollection* YoloPluginCreator::getFieldNames()
    {
        return &mFC;
    }

    IPluginV2IOExt* YoloPluginCreator::createPlugin(const char* name, const PluginFieldCollection* fc)
    {
        assert(!strcmp(name, getPluginName()));
        const PluginField* fields = fc->fields;
        int yolo_width, yolo_height, num_anchors = 0;
        float anchors[MAX_ANCHORS * 2];
        int num_classes, input_multiplier, new_coords = 0;
        float scale_x_y = 1.0;

        for (int i = 0; i < fc->nbFields; ++i)
        {
            const char* attrName = fields[i].name;
            if (!strcmp(attrName, "yoloWidth"))
            {
                assert(fields[i].type == PluginFieldType::kINT32);
                yolo_width = *(static_cast<const int*>(fields[i].data));
            }
            else if (!strcmp(attrName, "yoloHeight"))
            {
                assert(fields[i].type == PluginFieldType::kINT32);
                yolo_height = *(static_cast<const int*>(fields[i].data));
            }
            else if (!strcmp(attrName, "numAnchors"))
            {
                assert(fields[i].type == PluginFieldType::kINT32);
                num_anchors = *(static_cast<const int*>(fields[i].data));
            }
            else if (!strcmp(attrName, "numClasses"))
            {
                assert(fields[i].type == PluginFieldType::kINT32);
                num_classes = *(static_cast<const int*>(fields[i].data));
            }
            else if (!strcmp(attrName, "inputMultiplier"))
            {
                assert(fields[i].type == PluginFieldType::kINT32);
                input_multiplier = *(static_cast<const int*>(fields[i].data));
            }
            else if (!strcmp(attrName, "anchors")){
                assert(num_anchors > 0 && num_anchors <= MAX_ANCHORS);
                assert(fields[i].type == PluginFieldType::kFLOAT32);
                memcpy(anchors, static_cast<const float*>(fields[i].data), num_anchors * 2 * sizeof(float));
            }
            else if (!strcmp(attrName, "scaleXY"))
            {
                assert(fields[i].type == PluginFieldType::kFLOAT32);
                scale_x_y = *(static_cast<const float*>(fields[i].data));
            }
            else if (!strcmp(attrName, "newCoords"))
            {
                assert(fields[i].type == PluginFieldType::kINT32);
                new_coords = *(static_cast<const int*>(fields[i].data));
            }
            else
            {
                std::cerr <<  "Unknown attribute: " << attrName << std::endl;
                assert(0);
            }
        }
        assert(yolo_width > 0 && yolo_height > 0);
        assert(anchors[0] > 0.0f && anchors[1] > 0.0f);
        assert(num_classes > 0);
        assert(input_multiplier == 8 || input_multiplier == 16 || input_multiplier == 32);
        assert(scale_x_y >= 1.0);

        YoloLayerPlugin* obj = new YoloLayerPlugin(yolo_width, yolo_height, num_anchors, anchors, num_classes, yolo_width * input_multiplier, yolo_height * input_multiplier, scale_x_y, new_coords);
        obj->setPluginNamespace(mNamespace.c_str());
        return obj;
    }

    IPluginV2IOExt* YoloPluginCreator::deserializePlugin(const char* name, const void* serialData, size_t serialLength)
    {
        YoloLayerPlugin* obj = new YoloLayerPlugin(serialData, serialLength);
        obj->setPluginNamespace(mNamespace.c_str());
        return obj;
    }

    PluginFieldCollection YoloPluginCreator::mFC{};
    std::vector<PluginField> YoloPluginCreator::mPluginAttributes;
    REGISTER_TENSORRT_PLUGIN(YoloPluginCreator);
} // namespace nvinfer1
