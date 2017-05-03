import unittest

from munininfluxdb.main import main

from . import mock


class TestMain(unittest.TestCase):

    def test_main(self):
        args = 'import'.split()
        mock_cmd = mock.MagicMock(NAME='import')
        mocked_commands = {
            'import': mock_cmd
        }
        with mock.patch('munininfluxdb.main.dummy_function') as fun:
            result = main(args, mocked_commands)
            mock_cmd.setup.assert_called()
            fun.assert_called()
        self.assertEqual(result, 0)
