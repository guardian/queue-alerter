from unittest2 import TestCase
from mock import MagicMock, patch, call
from requests.auth import HTTPBasicAuth
from requests.models import Response
import json


class TestRabbitMQConfig(TestCase):
    def test_load_from_file(self):
        """
        load_from_files should open files at the indicated location and return an initialised RabbitMQConfig
        :return:
        """
        from alerter.rabbitmq_admin import RabbitMQConfig

        result = RabbitMQConfig.load_from_files("test_data/load_from_file_ok", True)
        self.assertEqual(result.host, "rmqhost")
        self.assertEqual(result.port, 15672)    #note that this should NOT be the port in the given URL
        self.assertEqual(result.vhost, "vhostname")
        self.assertEqual(result.ssl, True)
        self.assertEqual(result.credentials, HTTPBasicAuth("uname","pwd"))

    def test_invalid_url(self):
        """
        load_from_files should raise an exception if the uri provided is not valid
        :return:
        """
        from alerter.rabbitmq_admin import RabbitMQConfig

        with self.assertRaises(ValueError):
            RabbitMQConfig.load_from_files("test_data/load_from_file_invalid", True)


class TestGetQueuedMessageCount(TestCase):
    def test_queued_messagecount_ok(self):
        """
        get_queued_message_count should make an http request to the indicated instance, extract the
        "messages_ready" field and return the result
        :return:
        """
        with open("test_data/sample.json", "r") as f:
            sample_content = json.loads(f.read())

        http_response = Response()
        http_response.status_code = 200
        http_response.json = MagicMock(return_value=sample_content)
        with patch("requests.get", return_value=http_response) as mock_get:
            from alerter.rabbitmq_admin import get_queued_message_count, RabbitMQConfig
            mqconfig = RabbitMQConfig("rabbitmq-host",None,"vhost",True,HTTPBasicAuth("user","password"))

            result = get_queued_message_count("somequeue", mqconfig)
            self.assertEqual(result, 121)

            mock_get.assert_called_once_with(
                "https://rabbitmq-host:15672/api/queues/vhost/somequeue",
                auth=HTTPBasicAuth("user","password")
            )

    def test_queued_messagecount_retry(self):
        """
        get_queued_message_count should retry the access on 503
        :return:
        """
        with open("test_data/sample.json", "r") as f:
            sample_content = json.loads(f.read())

        http_responses = [Response(), Response()]
        http_responses[0].status_code = 503
        http_responses[1].status_code = 200
        http_responses[1].json = MagicMock(return_value=sample_content)

        with patch("requests.get", side_effect=http_responses) as mock_get:
            from alerter.rabbitmq_admin import get_queued_message_count, RabbitMQConfig
            mqconfig = RabbitMQConfig("rabbitmq-host",None,"vhost",True,HTTPBasicAuth("user","password"))

            result = get_queued_message_count("somequeue", mqconfig)
            self.assertEqual(result, 121)

            mock_get.assert_has_calls([
                call(
                    "https://rabbitmq-host:15672/api/queues/vhost/somequeue",
                    auth=HTTPBasicAuth("user","password")
                ),
                call(
                    "https://rabbitmq-host:15672/api/queues/vhost/somequeue",
                    auth=HTTPBasicAuth("user","password")
                )
                ]
            )
            self.assertEqual(mock_get.call_count, 2)

    def test_queued_messagecount_denied(self):
        """
        get_queued_message_count should raise an error on 403
        :return:
        """
        with open("test_data/sample.json", "r") as f:
            sample_content = json.loads(f.read())

        http_response = Response()
        http_response.status_code = 403
        http_response.json = MagicMock(return_value=sample_content)

        with patch("requests.get", return_value=http_response) as mock_get:
            from alerter.rabbitmq_admin import get_queued_message_count, RabbitMQConfig
            mqconfig = RabbitMQConfig("rabbitmq-host",None,"vhost",True,HTTPBasicAuth("user","password"))

            with self.assertRaises(RuntimeError):
                get_queued_message_count("somequeue", mqconfig)

            mock_get.assert_called_once_with(
                "https://rabbitmq-host:15672/api/queues/vhost/somequeue",
                auth=HTTPBasicAuth("user","password")
            )