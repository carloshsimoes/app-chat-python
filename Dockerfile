FROM ubuntu

ADD . /api
WORKDIR /api

RUN apt update \
 && apt upgrade -y \
 && apt install python3 pip -y \
 && chmod +x /api/runAPI.sh

EXPOSE 8888

ENTRYPOINT [ "sh", "/api/runAPI.sh" ]
