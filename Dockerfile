FROM centos:7
MAINTAINER ferr <f@minimoo.eu>
LABEL version="1.0"
LABEL description="Mikrotik DHCP DNS Updater"

ENV container docker
#ENV init /lib/systemd/systemd
ENV LC_ALL C

RUN yum update -y; yum install -y python-flask bind-utils;
RUN yum clean all;

ADD mikrotik.py /mikrotik.py
RUN chmod 755 /mikrotik.py

EXPOSE 5000

CMD ["/mikrotik.py"]

HEALTHCHECK --interval=5m --timeout=3s CMD curl localhost:5000 | grep Mikrotik || exit 1

