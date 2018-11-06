LOCAL_PATH:= $(call my-dir)

include $(CLEAR_VARS)

LOCAL_MODULE:= android_native_app_glue
LOCAL_SRC_FILES:= android_native_app_glue.c
LOCAL_EXPORT_C_INCLUDES := $(LOCAL_PATH)
LOCAL_EXPORT_LDLIBS := -llog -landroid
# The linker will strip this as "unused" since this is a static library, but we
# need to keep it around since it's the interface for JNI.
LOCAL_EXPORT_LDFLAGS := -u ANativeActivity_onCreate

include $(BUILD_STATIC_LIBRARY)
