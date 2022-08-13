#!/bin/bash
echo "============="
echo "Install FFMPEG"
echo "What build of FFMPEG do you require?"
echo "If you don't know check your CPU specs for a hint."
echo "- 32bit"
echo "- 64bit"
echo "- armel-32bit"
echo "- armhf-32bit"
read ffmpegbuild
wget "https://s3.amazonaws.com/cloudcamio/ffmpeg-release-$ffmpegbuild-static.tar.xz"
tar xf "ffmpeg-release-$ffmpegbuild-static.tar.xz"
mv "ffmpeg-3.3-$ffmpegbuild-static/ffmpeg" "/usr/bin/ffmpeg"
mv "ffmpeg-3.3-$ffmpegbuild-static/ffmpeg-10bit" "/usr/bin/ffmpeg-10bit"
mv "ffmpeg-3.3-$ffmpegbuild-static/ffprobe" "/usr/bin/ffprobe"
mv "ffmpeg-3.3-$ffmpegbuild-static/ffserver" "/usr/bin/ffserver"
chmod +x /usr/bin/ffmpeg
chmod +x /usr/bin/ffmpeg-10bit
chmod +x /usr/bin/ffprobe
chmod +x /usr/bin/ffserver
rm -rf "ffmpeg-3.3-$ffmpegbuild-static"
rm -rf "ffmpeg-release-$ffmpegbuild-static.tar.xz"
