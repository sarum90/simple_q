#######################################################
#     Dockerfile for running my little python service
#######################################################

FROM ubuntu

MAINTAINER Marcus Ewert

RUN apt-get update && apt-get install -y python python-pip python-dev

RUN pip install mock twisted

ADD src /myapp

ENV PORT 8080

EXPOSE 8080

WORKDIR /myapp
