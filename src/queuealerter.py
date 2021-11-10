#!/usr/bin/env python3
import os
from rabbitmq_admin import RabbitMQConfig, get_queued_message_count
from pagerduty import notify_pagerduty
import yaml
import logging
import time

logger = logging.getLogger(__name__)


def run_check(config: list):
    rmqpath = os.environ.get("RABBITMQ_CONFIG_PATH")
    if rmqpath is None or rmqpath=="":
        raise ValueError("You must specify RABBITMQ_CONFIG_PATH to indicate where the rabbitmq_client_uri file is located")
    no_ssl = os.environ.get("RABBITMQ_NO_SSL")
    use_ssl = no_ssl.lower() != "true"

    rmqconfig = RabbitMQConfig.load_from_files(rmqpath, use_ssl)
    for entry in config:
        current_messages = get_queued_message_count(entry["queuename"], rmqconfig)
        logger.info("Currently there are {0} messages on the {1} queue".format(current_messages, entry["queuename"]))
        if current_messages > entry["threshold"]:
            logger.warning("{0} is over the threshold of {1} so alerting...".format(entry["queuename"], entry["threshold"]))
            msg = "The queue {0} currently has {1} messages which exceeds the alert threshold. Please investigate."
            notify_pagerduty(msg, "trigger", "queuesize-{0}".format(entry["queuename"]), current_messages)


def validate_config(config: list):
    """
    checks that the provided dictionary (parsed from yaml) is in fact a valid configuration.
    Raises a ValueError if not.
    :param config:
    :return:
    """
    if not isinstance(config, list):
        raise ValueError("Configuration is invalid, the root element should be a list")
    i = 0
    for entry in config:
        if not isinstance(entry, dict):
            raise ValueError("Configuration is invalid, entry {0} is not an object".format(i))
        if "queue" not in entry:
            raise ValueError("Configuration is invalid, entry {0} does not specify 'queue'".format(i))
        if not isinstance(entry["queue"], str):
            raise ValueError("Configuration is invalid, entry {0} 'queue' is not a string")
        if "threshold" not in entry:
            raise ValueError("Configuration is invalid, entry {0} does not specify 'threshold'".format(i))
        if not isinstance(entry["threshold"], int):
            raise ValueError("Configuration is invalid, entry {0} 'thresold' is not an integer")
        i += 1


if __name__ == "__main__":
    sleeptime = os.environ.get("CHECK_EVERY")
    if sleeptime is None or sleeptime=="":
        sleeptime = 300
    else:
        sleeptime = int(sleeptime)

    configpath = os.environ.get("APP_CONFIG")
    if configpath is None or configpath=="":
        raise ValueError("You must specify APP_CONFIG to indicate a YAML file containing the application config")

    with open(configpath, "r") as f:
        appconfig = yaml.safe_load(f)

    validate_config(appconfig)

    while True:
        run_check(appconfig)
        time.sleep(sleeptime)
