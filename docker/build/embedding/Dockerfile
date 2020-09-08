FROM shareai/tensorflow:armv7l_tf1.8

RUN mkdir -p /root/.ssh
COPY ./id_rsa /root/.ssh/id_rsa
RUN chmod 600 /root/.ssh/id_rsa
COPY ./sshconfig /root/.ssh/config

RUN ls -lh && apt-get update && apt-get install -y libopenblas-base && apt-get clean && \
    mkdir -p /root/.local/lib/python2.7/site-packages/

COPY ./requirements.txt /root/requirements.txt
RUN pip install -r /root/requirements.txt

