#!/bin/bash

for CPU_NUM in {0..7}; do echo $CPU_NUM;
   MAX_FREQ=`cat /sys/devices/system/cpu/cpu$CPU_NUM/cpufreq/cpuinfo_max_freq`
   echo $MAX_FREQ
   echo $MAX_FREQ > /sys/devices/system/cpu/cpu$CPU_NUM/cpufreq/scaling_max_freq
   echo $MAX_FREQ > /sys/devices/system/cpu/cpu$CPU_NUM/cpufreq/scaling_min_freq
done

