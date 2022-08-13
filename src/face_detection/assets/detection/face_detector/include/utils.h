#ifndef __UTILS_H__
#define __UTILS_H__

#include <sys/time.h>
#include <string>
#include <vector>


float getElapse(struct timeval *tv1,struct timeval *tv2);

int trave_dir(std::string& path, std::vector<std::string>& file_list);

#endif