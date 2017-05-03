import unittest
from pprint import pprint

from .. import mock

import munininfluxdb.commands.fetch as m_fetch


class TestFetch(unittest.TestCase):

    def setUp(self):
        self.patchers = set()
        self.mocks = {}

        for name in 'print Defaults influxdb storable'.split():
            patcher = mock.patch('munininfluxdb.commands.fetch.%s' % name)
            self.patchers.add(patcher)
            self.mocks[name] = patcher.start()

    def tearDown(self):
        for name, mock_ in self.mocks.items():
            print(name.center(40, '-'))
            pprint(mock_.mock_calls)
        for patcher in self.patchers:
            patcher.stop()

    def test_pack_values(self):
        config = {
            'metrics': {
                'metric_a': ('measurement_a', 'field_a'),
            },
            'tags': {
                'measurement_a': ['tag_a']
            },
        }
        metric_a = mock.MagicMock()
        metric_a.values.return_value = ((123, 10), (234, 11))
        metric_b = mock.MagicMock()
        metric_b.values.return_value = ((345, 13), (456, 8))
        values = (
            {
                'metric_a': metric_a,
                'metric_b': metric_b,
            },
            12345  # unix timestamp
        )
        result = m_fetch.pack_values(config, values)

        expected = [
            {'fields': {'field_a': 10.0},
             'measurement': 'measurement_a',
             'tags': ['tag_a'],
             'time': 123}
        ]
        self.assertEqual(result, expected)

    def test_read_state_file(self):
        self.mocks['storable'].retrieve.return_value = {
            'spoolfetch': 'spoolfetch-value',
            'value': 'myvalue'
        }
        result = m_fetch.read_state_file('my-state-file')
        expected = ('myvalue', 'spoolfetch-value')
        self.assertEqual(result, expected)

    def test_main(self):
        mocked_args = mock.MagicMock(name='mock-args')
        with mock.patch('munininfluxdb.commands.fetch.open', create=True), \
                mock.patch('munininfluxdb.commands.fetch.json') as m_json, \
                mock.patch('munininfluxdb.commands.fetch.pack_values') as m_pd, \
                mock.patch('munininfluxdb.commands.fetch.read_state_file'):
            m_pd.return_value = [1, 2, 3]  # just a dummy value
            m_json.load.return_value = {
                'influxdb': {
                    'host': 'influxdb.host',
                    'user': 'influxdb.user',
                    'port': 'influxdb.port',
                    'password': 'influxdb.password',
                    'database': 'influxdb.database',
                },
                'statefiles': ['statefile-1'],
                'lastupdate': 'lastupdate-value'
            }
            result = m_fetch.main(mocked_args)

        # --- Verify calls ------------------
        self.mocks['influxdb'].InfluxDBClient.assert_called_with(
            'influxdb.host', 'influxdb.port', 'influxdb.user',
            'influxdb.password',
        )

        idbclient = self.mocks['influxdb'].InfluxDBClient()
        idbclient.get_list_database.assert_called_with()
        idbclient.switch_database.assert_called_with('influxdb.database')
        idbclient.write_points.assert_called_with(
            m_pd.return_value,
            time_precision='s'
        )
        self.assertIsNone(result)

    def test_setup(self):
        from argparse import ArgumentParser

        self.mocks['Defaults'].FETCH_CONFIG = 'foo'

        parser = ArgumentParser()
        m_fetch.setup(parser, {})

        result = parser.parse_args(''.split())
        self.assertEqual(result.config, 'foo')

        result = parser.parse_args('--config bar'.split())
        self.assertEqual(result.config, 'bar')
