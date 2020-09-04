FROM arm32v7/debian:stretch

RUN apt-get update && apt-get install -y cmake liblog4cpp5-dev libv4l-dev
RUN apt-get install -y git
RUN apt-get install -y build-essential
RUN git clone https://github.com/mpromonet/v4l2rtspserver.git && \
    cd v4l2rtspserver/ && \
    cmake . && \
    make && \
    make install
