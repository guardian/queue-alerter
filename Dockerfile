FROM python:3.10-alpine

COPY requirements.txt /tmp
RUN pip install -r /tmp/requirements.txt
COPY src/dist/queuealerter-1.0.tar.gz /
RUN cd /tmp && tar xzf /queuealerter-1.0.tar.gz && cd queuealerter-1.0/ && python ./setup.py install && cd / && rm -rf /tmp/queuealerter-1.0/
USER nobody
CMD /usr/local/bin/queuealerter.py
