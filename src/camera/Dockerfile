#FROM mhart/alpine-node:8
#FROM arm64v8/node:8-alpine
FROM shareai/tensorflow:armv7l_tf1.8


# Install package dependencies
RUN apt-get update && \
    apt-get install -y pkg-config graphicsmagick curl sqlite3 libsqlite3-dev libcairo2-dev libgif-dev && \
    curl -sL https://deb.nodesource.com/setup_8.x | bash - && \
    apt-get update && apt-get install -y nodejs libdrm-dev && apt-get clean

WORKDIR /opt/
COPY ./nvr_releases/2018.03.15.14.50.tar.gz /opt/2018.03.15.14.50.tar.gz

RUN mkdir -p /opt/nvr && tar -zxf 2018.03.15.14.50.tar.gz && mv Shinobi-2018.03.15.14.50/* /opt/nvr/ && \
    rm -rf /opt/Shinobi-2018.03.15.14.50/ && cd /opt/nvr && \
    # Install NodeJS dependencies
    npm install && \
    npm install canvas@1.6 moment ffmpeg-static --unsafe-perm && \
    rm /root/.npm/* -rf && \
    rm -rf Shinobi-Shinobi-2018.03.15.14.50 

ADD nvr_releases/2018.03.15.14.50_patchs/* /opt/nvr/

ADD docker-entrypoint.sh /opt/nvr/docker-entrypoint.sh
ADD conf.d/main.conf.json /opt/nvr/conf.json
ADD conf.d/super.json /opt/nvr/super.json
ADD ./detector /opt/nvr/detector

WORKDIR /opt/nvr/detector
RUN npm install && npm run build && cp dist/release/* . -a && cp dist/release/libs/* ./libs/ -a && rm -rf dist && rm -rf uglifyjs-es-cmd \
    rm /opt/2018.03.15.14.50.tar.gz && apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* && \
    cp /etc/apt/sources.list.bk /etc/apt/sources.list && \
    rm /root/.npm/* -rf

WORKDIR /opt/nvr
COPY sql/conf.sqlite sql/shinobi.sample.sqlite
RUN cp sql/shinobi.sample.sqlite /opt/nvr/conf.sqlite
VOLUME ["/opt/nvr/videos"]

EXPOSE 8080
ENTRYPOINT ["/opt/nvr/docker-entrypoint.sh" ]
