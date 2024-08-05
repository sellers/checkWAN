FROM python:3

WORKDIR /

RUN python setup.py

RUN WHERE DO I GET THE DOCKER CFG DATA FROM?
CMD [/usr/bin/checkwan]
