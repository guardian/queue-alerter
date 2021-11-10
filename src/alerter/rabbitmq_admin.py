import requests
import requests.auth
import logging
import time
from typing import Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)
logger.level = logging.INFO


class RabbitMQConfig(object):
    def __init__(self, host: str, port: Optional[int], vhost:str, ssl:bool, credentials: requests.auth.AuthBase):
        self.host = host
        if port is None:
            self.port = 15672
        else:
            self.port = port
        self.vhost = vhost
        self.ssl = ssl

        self.credentials = credentials

    def make_url(self, section:str, url_tail:str) -> str:
        if self.ssl:
            proto = "https"
        else:
            proto = "http"
        return "{0}://{1}:{2}/api/{3}/{4}/{5}".format(proto, self.host, self.port, section, self.vhost, url_tail)

    @staticmethod
    def load_from_files(filepath: str, want_ssl: bool):
        """
        Initialises RabbitMQ config from text files in a directory.  This is intended to be used from Kubernetes,
        where we can mount a secrets manifest as a directory path and read its contents from files.
        :param filepath: directory to load the files from. An IOError will be raised if any of the expected files do not exist here.
        :param want_ssl: if this is set, then use HTTPS for accessing the management port (recommended!)
        :return: a RabbitMQConfig object. Raises an exception if there is an error.
        """
        with open(filepath + "/rabbitmq_client_uri", "r") as f:
            content = f.read()
            parsed_url = urlparse(content)

        if parsed_url.scheme != "amqp":
            logger.error("Expected rabbitmq uri scheme to be 'amqp' but got {0}".format(parsed_url.scheme))
            raise ValueError("scheme is incorrect")
        if parsed_url.path == "":
            logger.error("Expected a virtualhost in the rabbitmq uri at {0}".format(filepath))
            raise ValueError("no virtualhost for rabbitmq")

        # we don't use the port from the parsed url as that is for the AMQP port not the management port
        return RabbitMQConfig(parsed_url.hostname, None, parsed_url.path.lstrip("/ "),
                              want_ssl,
                              requests.auth.HTTPBasicAuth(parsed_url.username, parsed_url.password)
                              )


def get_queued_message_count(queue_name: str, config: RabbitMQConfig, retry_limit=10, retry_counter=0) -> int:
    """
    requests the current message count for the given queue from the server.
    :param queue_name: name of the queue to request
    :param config: RabbitMQConfig
    :param retry_limit: maximum number of times to retry, defaults to 10
    :param retry_counter: current retry counter. Don't specify this when calling
    :return: the queued message count. Throws an exception on failure and will retry on transient errors
    """
    if retry_counter > retry_limit:
        logger.error("Could not succeed after {0} attempts, giving up".format(retry_counter))
        raise RuntimeError("Could not contact RabbitMQ and exhausted retries")

    dest_url = config.make_url("queues", queue_name)
    logger.debug("Making request to {0}".format(dest_url))

    response = requests.get(dest_url, auth=config.credentials)
    if response.status_code == 200:
        content = response.json()
        return content["messages_ready"]
    elif response.status_code == 503 or response.status_code == 504:
        logger.warning("Rabbit MQ is not available at the moment ({0} returned 503). Retrying in a few seconds...")
        time.sleep(3)
        return get_queued_message_count(queue_name, config, retry_limit, retry_counter+1)
    else:
        logger.error("Could not contact RabbitMQ at {0}, server returned {1} {2}".format(dest_url, response.status_code, response.text))
        raise RuntimeError("RabbitMQ returned an error, see the logs for details")

