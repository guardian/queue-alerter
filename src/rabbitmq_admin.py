import requests
import requests.auth
from typing import Optional


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

def get_queued_message_count(queue_name: str, config: RabbitMQConfig):
    """
    requests the current message count for the given queue from the server.
    :param queue_name: name of the queue to request
    :param config: RabbitMQConfig
    :return: the queued message count. Throws an exception on failure and will retry on transient errors
    """

    requests.get()