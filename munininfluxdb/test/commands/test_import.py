import unittest
from pprint import pprint

from .. import mock

import munininfluxdb.commands.import_ as m_import


class TestImport(unittest.TestCase):

    def setUp(self):
        self.patchers = set()
        self.mocks = {}

        for name in 'print munin rrd Settings InfluxdbClient Dashboard prompt ask_password raw_input'.split():
            patcher = mock.patch('munininfluxdb.commands.import_.%s' % name)
            self.patchers.add(patcher)
            self.mocks[name] = patcher.start()

    def tearDown(self):
        for name, mock_ in self.mocks.items():
            print(name.center(40, '-'))
            pprint(mock_.mock_calls)
        for patcher in self.patchers:
            patcher.stop()

    def test_main(self):
        args = mock.MagicMock(name='cli-args')

        # --- prime mocks -----------------------
        settings = mock.MagicMock(
            name='settings',
            paths={
                'xml': 'xmlpath',
                'fetch_config': 'fcpath',
            },
            interactive=False,
            influxdb={
                'password': 'idbpwd',
                'database': 'idbdb',
                'host': 'idbhost',
                'group_fields': True,
            },
            grafana={
                'host': 'grafanahost',
                'create': True,
                'filename': 'grafanafile',
            }
        )
        dashboard = mock.MagicMock(name='dashboard')
        self.mocks['Dashboard'].return_value = dashboard
        self.mocks['Settings'].return_value = settings
        self.mocks['rrd'].export_to_xml.return_value = 10
        exporter = mock.MagicMock(name='InfluxdbClient', settings=settings)
        exporter.get_settings.return_value = settings
        self.mocks['InfluxdbClient'].return_value = exporter

        # --- make the call ---------------------
        m_import.main(args)

        # --- verify calls ----------------------
        exporter.connect.assert_called()
        exporter.test_db.assert_called_with('idbdb')
        exporter.import_from_xml.assert_called()
        exporter.get_settings.assert_called()

        settings.save_fetch_config.assert_called()

        dashboard.generate.assert_called()
        dashboard.upload.assert_called()
        dashboard.save.assert_called()

    def test_setup(self):
        from argparse import ArgumentParser

        parser = ArgumentParser()
        m_import.setup(parser, {})

        # Default values
        result = parser.parse_args(''.split())

        self.assertEqual(result.grafana_cols, 2)
        self.assertEqual(result.grafana_file,
                         '/tmp/munin-influxdb/munin-grafana.json')
        self.assertEqual(result.grafana_title, 'Munin Dashboard')
        self.assertEqual(result.influxdb, 'root@localhost:8086/db/munin')
        self.assertEqual(result.munin_path, '/var/lib/munin')
        self.assertEqual(result.rrd, '/var/lib/munin')
        self.assertEqual(result.verbose, 1)
        self.assertEqual(result.www, '/var/cache/munin/www')
        self.assertEqual(result.xml_temp_path, '/tmp/munin-influxdb/xml')
        self.assertFalse(result.keep_temp)

        self.assertIsNone(result.grafana_tags)

        self.assertEqual(result.rrd, '/var/lib/munin')
        self.assertEqual(result.www, '/var/cache/munin/www')
        self.assertTrue(result.fetch_config_path.endswith(
            '.config/munin-fetch-config.json'))
        self.assertTrue(result.grafana)
        self.assertTrue(result.group_fields)
        self.assertTrue(result.show_minmax)

        # The above also checks that the values appear properly in the resulting
        # namespace.
        # TODO We should also test passing in other values and verify that they
        #      are properly checked. I'll skip this for now in order to advance.
