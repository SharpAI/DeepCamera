FROM arm64v8/node:8-alpine

WORKDIR /opt/
ADD ./package.json /opt/package.json
RUN npm install

ADD ./index.js /opt/index.js
ADD ./run.sh /opt/run.sh

EXPOSE 8080
