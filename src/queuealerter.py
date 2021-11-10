#!/usr/bin/env python3
import os
from alerter.rabbitmq_admin import RabbitMQConfig, get_queued_message_count
from alerter.pagerduty import notify_pagerduty
import yaml
import logging
import time

LOGFORMAT = '%(asctime)s %(name)s|%(funcName)s [%(levelname)s] %(message)s'
logging.basicConfig(format=LOGFORMAT, level=logging.WARNING)
logger = logging.getLogger(__name__)
logger.level = logging.INFO

def run_check(config: list):
    if os.environ.get("SERVICE_KEY") is None or os.environ.get("SERVICE_KEY")=="":
        raise ValueError("You must specify SERVICE_KEY to indicate the PagerDuty service key to send alerts to")

    rmqpath = os.environ.get("RABBITMQ_CONFIG_PATH")
    if rmqpath is None or rmqpath == "":
        raise ValueError("You must specify RABBITMQ_CONFIG_PATH to indicate where the rabbitmq_client_uri file is located")

    no_ssl = os.environ.get("RABBITMQ_NO_SSL")
    if no_ssl is None:
        use_ssl = True
    else:
        use_ssl = no_ssl.lower() != "true"

    rmqconfig = RabbitMQConfig.load_from_files(rmqpath, use_ssl)
    for entry in config:
        current_messages = get_queued_message_count(entry["queue"], rmqconfig)
        logger.info("Currently there are {0} messages on the {1} queue".format(current_messages, entry["queue"]))
        if current_messages > entry["threshold"]:
            logger.warning("{0} is over the threshold of {1} so alerting...".format(entry["queue"], entry["threshold"]))
            msg = "The queue {0} currently has {1} messages which exceeds the alert threshold. Please investigate.".format(entry["queue"], current_messages)
            notify_pagerduty(msg, "trigger", "queuesize-{0}".format(entry["queue"]), current_messages)


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

    logger.info("Starting up queue-alerter, monitoring {0} queues every {1} seconds:".format(len(appconfig), sleeptime))
    for entry in appconfig:
        logger.info("\t{0}: alert if more than {1} messages waiting".format(entry["queue"], entry["threshold"]))

    while True:
        run_check(appconfig)
        time.sleep(sleeptime)
