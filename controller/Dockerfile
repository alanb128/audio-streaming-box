FROM balenalib/raspberrypi3-ubuntu-python:3.9-focal-build-20230530

WORKDIR /usr/src/app

RUN \
    pip3 install flask requests adafruit-circuitpython-charlcd pad4pi adafruit-circuitpython-seesaw

COPY *.py ./

CMD ["python3", "flask-api.py"]
