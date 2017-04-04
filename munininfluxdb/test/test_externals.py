"""
Tests for external dependencies/external systems.

This module makes use of mock to "simulate" the external calls. If "mock" is
unavailable, the tests are skipped.
"""
import unittest

from . import mock


@unittest.skipUnless(mock, "unittest.mock is not available.")
class TestCron(unittest.TestCase):
    """
    Test Case for CRON commands.
    """

    def test_install(self):
        from munininfluxdb.external import cron
        with mock.patch('munininfluxdb.external.cron.crontab') as ptch:
            cron_instance = mock.MagicMock()
            ptch.CronTab.return_value = cron_instance

            cmd_instance = mock.MagicMock()
            cmd_instance.is_valid.return_value = True
            cmd_instance.is_enabled.return_value = True
            cron_instance.new.return_value = cmd_instance

            result = cron.add_with_comment('munin', 'foo bar', 10, 'hoi')
            ptch.CronTab.assert_called_with(user='munin')
            cron_instance.new.assert_called_with(
                command='foo bar',
                comment='hoi',
                user='munin')

            cmd_instance.minute.every.assert_called_with(10)
        self.assertTrue(result)

    def test_uninstall(self):
        from munininfluxdb.external import cron
        with mock.patch('munininfluxdb.external.cron.crontab') as ptch:
            cron_instance = mock.MagicMock()
            ptch.CronTab.return_value = cron_instance

            cron_instance.find_comment.return_value = [1, 2, 3]

            result = cron.remove_by_comment('munin', 'hoi')

            ptch.CronTab.assert_called_with(user='munin')
            cron_instance.find_comment.assert_called_with('hoi')
            cron_instance.remove.assert_called_with(1, 2, 3)
            cron_instance.write.assert_called_with()

        self.assertEqual(result, 3)
