import unittest
from pprint import pprint

from .. import mock

import munininfluxdb.commands.dump as m_dump


class TestDump(unittest.TestCase):

    def setUp(self):
        self.patchers = set()
        self.mocks = {}
        for name in 'print munin rrd Settings Defaults Symbol'.split():
            patcher = mock.patch('munininfluxdb.commands.dump.%s' % name)
            self.patchers.add(patcher)
            self.mocks[name] = patcher.start()

    def tearDown(self):
        for name, mock_ in self.mocks.items():
            print(name.center(40, '-'))
            pprint(mock_.mock_calls)
        for patcher in self.patchers:
            patcher.stop()

    def test_retrieve_munin_configuration(self):
        mock_settings = mock.MagicMock(name='mock-settings',
                                       paths={'datafile': 'the-datafile'})
        self.mocks['munin'].discover_from_datafile.return_value = mock_settings

        m_dump.retrieve_munin_configuration(mock_settings)

        self.mocks['munin'].discover_from_datafile.assert_called_with(
            mock_settings)
        self.mocks['rrd'].check_rrd_files.assert_called_with(mock_settings)

    def test_main(self):
        token = object()
        mock_settings = mock.MagicMock()
        self.mocks['Settings'].return_value = mock_settings
        self.mocks['munin'].discover_from_datafile.return_value = mock_settings

        m_dump.main(token)

        self.mocks['Settings'].assert_called_with(token)
        self.mocks['munin'].discover_from_datafile.assert_called_with(
            mock_settings)
        self.mocks['rrd'].export_to_xml.assert_called_with(mock_settings)

    def test_setup(self):
        from argparse import ArgumentParser

        self.mocks['Defaults'].MUNIN_VAR_FOLDER = 'mvf'
        self.mocks['Defaults'].MUNIN_RRD_FOLDER = 'mrf'
        self.mocks['Defaults'].MUNIN_WWW_FOLDER = 'mwf'
        self.mocks['Defaults'].MUNIN_XML_FOLDER = 'mxf'

        parser = ArgumentParser()
        m_dump.setup(parser, {})

        result = parser.parse_args(''.split())
        self.assertEqual(result.xml_temp_path, 'mxf')
        self.assertEqual(result.keep_temp, False)
        self.assertEqual(result.verbose, 1)
        self.assertEqual(result.munin_path, 'mvf')
        self.assertEqual(result.www, 'mwf')
        self.assertEqual(result.rrd, 'mrf')
