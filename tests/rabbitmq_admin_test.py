from unittest2 import TestCase
from mock import MagicMock, patch
from requests.auth import HTTPBasicAuth


class TestRabbitMQConfig(TestCase):
    def test_load_from_file(self):
        """
        load_from_files should open files at the indicated location and return an initialised RabbitMQConfig
        :return:
        """
        from rabbitmq_admin import RabbitMQConfig

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
        from rabbitmq_admin import RabbitMQConfig

        with self.assertRaises(ValueError):
            RabbitMQConfig.load_from_files("test_data/load_from_file_invalid", True)
