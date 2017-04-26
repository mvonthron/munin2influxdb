import unittest

from .. import mock

import munininfluxdb.commands.cron as m_cron


class TestCron(unittest.TestCase):

    def setUp(self):
        self.pwd_patcher = mock.patch('munininfluxdb.commands.cron.pwd')
        self.os_patcher = mock.patch('munininfluxdb.commands.cron.os')
        self.sys_patcher = mock.patch('munininfluxdb.commands.cron.sys')
        self.print_patcher = mock.patch('munininfluxdb.commands.cron.print')

        self.__pwd = self.pwd_patcher.start()
        self.__os = self.os_patcher.start()
        self.__sys = self.sys_patcher.start()
        self.__print = self.print_patcher.start()

    def tearDown(self):
        self.pwd_patcher.stop()
        self.os_patcher.stop()
        self.sys_patcher.stop()
        self.print_patcher.stop()

    def test_get_cron_user_munin(self):
        result = m_cron.get_cron_user()
        self.assertEqual(result, 'munin')

    def test_get_cron_user_root(self):
        self.__pwd.getpwnam.side_effect = KeyError('token exception')
        result = m_cron.get_cron_user()
        self.assertEqual(result, 'root')

    def test_uninstall_cron(self):
        mock_cron = mock.MagicMock()
        fun = m_cron.uninstall_cron(mock_cron)
        args = mock.MagicMock(
            user='munin'
        )
        fun(args)
        mock_cron.remove_by_comment.assert_called_with(
            'munin', m_cron.CRON_COMMENT)

    def test_install_cron(self):
        mock_cron = mock.MagicMock()
        fun = m_cron.install_cron(mock_cron)
        args = mock.MagicMock(
            user='munin',
            period='5'
        )
        with mock.patch('munininfluxdb.commands.cron.absolute_executable') as p:
            p.return_value = '/foo/bar'
            fun(args)
        mock_cron.add_with_comment.assert_called_with(
            'munin', '/foo/bar fetch', '5', m_cron.CRON_COMMENT)

    def test_setup(self):
        from argparse import ArgumentParser
        parser = ArgumentParser()
        injections = {
            'cron': mock.MagicMock()
        }
        m_cron.setup(parser, injections)

        result = parser.parse_args('-u jdoe install -p 10'.split())
        self.assertEqual(result.period, 10)
        self.assertEqual(result.user, 'jdoe')

        result2 = parser.parse_args('-u jdoe uninstall'.split())
        self.assertEqual(result2.user, 'jdoe')
