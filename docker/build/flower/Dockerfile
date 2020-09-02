#FROM aarch64/python:2.7-alpine
FROM shareai/tensorflow:armv7l_tf1.8

# Get latest root certificates
#RUN apk add --update ca-certificates && update-ca-certificates

# Install the required packages
RUN pip install redis
RUN pip install https://github.com/mher/flower/zipball/master

# PYTHONUNBUFFERED: Force stdin, stdout and stderr to be totally unbuffered. (equivalent to `python -u`)
# PYTHONHASHSEED: Enable hash randomization (equivalent to `python -R`)
# PYTHONDONTWRITEBYTECODE: Do not write byte files to disk, since we maintain it as readonly. (equivalent to `python -B`)
ENV PYTHONUNBUFFERED=1 PYTHONHASHSEED=random PYTHONDONTWRITEBYTECODE=1

RUN rm -rf /tmp/* /var/tmp/* && \
    rm -rf /root/.cache/pip/

# Default port
EXPOSE 5555

# Run as a non-root user by default, run as user with least privileges.
USER nobody

ENTRYPOINT ["flower"]
