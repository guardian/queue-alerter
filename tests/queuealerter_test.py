import os

from unittest2 import TestCase
from mock import MagicMock, patch, call


class TestRunCheck(TestCase):
    def test_run_check(self):
        """
        run_check should call out to pagerduty only if a threshold is breached
        :return:
        """
        os.environ["SERVICE_KEY"] = "skey"
        os.environ["RABBITMQ_CONFIG_PATH"] = "/path/to/rabbitmq"

        loaded_rmq_config = MagicMock()

        with patch("alerter.rabbitmq_admin.RabbitMQConfig") as mock_rabbitmq_config:
            mock_rabbitmq_config.load_from_files = MagicMock(return_value=loaded_rmq_config)
            with patch("alerter.pagerduty.notify_pagerduty") as mock_notify_pd:
                with patch("alerter.rabbitmq_admin.get_queued_message_count", return_value=5) as mock_get_count:
                    from queuealerter import run_check

                    config = [
                        {"queue":"first_queue","threshold":0},
                        {"queue":"second_queue","threshold":10}
                    ]

                    run_check(config)
                    mock_notify_pd.assert_called_once_with(
                        "The queue first_queue currently has 5 messages which exceeds the alert threshold. Please investigate.",
                        "trigger",
                        "queuesize-first_queue",
                        5
                    )
                    self.assertEqual(mock_notify_pd.call_count, 1)

                    mock_get_count.assert_has_calls([
                        call("first_queue", loaded_rmq_config),
                        call("second_queue", loaded_rmq_config)
                    ])
                    self.assertEqual(mock_get_count.call_count, 2)
