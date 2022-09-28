FROM homeassistant/home-assistant:2022.8
ADD ./sharpai /usr/src/homeassistant/homeassistant/components/sharpai

RUN apk --update add libxml2-dev libxslt-dev libffi-dev gcc musl-dev libgcc openssl-dev curl
RUN apk add jpeg-dev zlib-dev freetype-dev lcms2-dev openjpeg-dev tiff-dev tk-dev tcl-dev
RUN pip install Pillow==9.2.0