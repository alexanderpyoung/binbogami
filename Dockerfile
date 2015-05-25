FROM ubuntu:14.04
MAINTAINER alexander@lxndryng.com

ENV DEBIAN_FRONTEND noninteractive
RUN apt-get update && apt-get -y upgrade && apt-get -y install python3 build-essential sqlite3 python3-pip python3-tk libxml2-dev libxslt-dev libjpeg-dev libpng-dev libfreetype6-dev libagg-dev libffi-dev pkg-config
ADD . /opt/binbogami
WORKDIR /opt/binbogami
RUN pip3 install -r requirements.txt
# Set up config
# THIS NEEDS CHANGING TO DEAL WITH POSTGRES
RUN cp /opt/binbogami/binbogami/bbg.cfg.sample /opt/binbogami/binbogami/bbg.cfg
RUN sed -i 's@{{database}}@\/opt\/binbogami\/bbg.db@g' /opt/binbogami/binbogami/bbg.cfg
RUN sed -i 's@{{secret_key}}@'$(openssl rand -hex 2048)'@g' /opt/binbogami/binbogami/bbg.cfg
RUN sed -i 's@{{upload_folder}}@\/opt\/binbogami\/files\/@g' /opt/binbogami/binbogami/bbg.cfg
RUN sed -i 's@{{debug}}@False@g' /opt/binbogami/binbogami/bbg.cfg
# Create necessary folders for file uploads (this should become based on ENVs)
RUN mkdir /opt/binbogami/files && mkdir /opt/binbogami/files/tmp
# Initialise sqlite db
RUN python3 docker_init.py
EXPOSE 5000
CMD ["/usr/bin/python3", "/opt/binbogami/runserver.py"]
# TODO: volume for files and db
