#!/usr/bin/python3

from distutils.core import setup

setup(
    name="queuealerter",
    version="1.0",
    description="Alert PagerDuty if rabbitmq queues breach limits",
    author="Andy Gallagher",
    author_email="andy.gallagher@theguardian.com",
    packages=["alerter"],
    scripts=["queuealerter.py"]
)
