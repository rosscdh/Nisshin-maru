FROM python:3-alpine

RUN apk add --no-cache python3-dev libstdc++ && \
    apk add --no-cache g++ && \
    ln -s /usr/include/locale.h /usr/include/xlocale.h && \
    pip3 install numpy && \
    pip3 install pandas requests alkali


WORKDIR /src

ADD . /src

ENTRYPOINT ["python"]

CMD ["instana-app-error-rate.py"]