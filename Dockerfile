FROM ubuntu

ADD . /app
WORKDIR /app

RUN apt update \
 && apt upgrade -y \
 && apt install python3 pip -y \
 && chmod +x /app/runAPP.sh

EXPOSE 8888

ENTRYPOINT [ "sh", "/app/runAPP.sh" ]
