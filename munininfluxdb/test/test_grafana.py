import unittest

import munininfluxdb.grafana as gf

from . import mock


DEFAULT_LINE_WIDTH = 1
DEFAULT_FILL = 5


class TestQuery(unittest.TestCase):

    def test_to_json(self):

        query = gf.Query(1.0, "thefield")
        result = query.to_json(None)

        expected = {
            "dsType": "influxdb",
            "measurement": 1.0,
            "select": [
                [
                    {"params": ["thefield"], "type": "field"},
                    {"params": [], "type": "mean"}
                ]
            ],
            "groupBy": [
                {"params": ["$interval"], "type": "time"},
                {"params": ["null"], "type": "fill"}
            ],
            "resultFormat": "time_series",
            "alias": "thefield"
        }

        self.assertEqual(result, expected)


class TestPanel(unittest.TestCase):

    def setUp(self):
        self.panel = gf.Panel(title="Hello", measurement=1.2)

    def test_add_query(self):
        self.assertEqual(len(self.panel.queries), 0)
        self.panel.add_query("thefield")
        self.assertEqual(len(self.panel.queries), 1)
        self.assertEqual(self.panel.queries[0].field, "thefield")

    @unittest.skipUnless(mock, "unittest.mock is not available.")
    def test_sort_queries(self):
        a = mock.MagicMock(name='11:30', field='11', field_2=30)
        b = mock.MagicMock(name='21:40', field='21', field_2=40)
        c = mock.MagicMock(name='10:20', field='10', field_2=20)
        d = mock.MagicMock(name='20:10', field='20', field_2=10)

        expected = [c, a, d, b]

        self.panel.queries = [a, b, c, d]
        self.panel.sort_queries('10 11 20 21')

        self.assertEqual(self.panel.queries, expected)

    def test_process_graph_settings(self):
        plugin_settings = {
            'graph_vlabel': 'vlabel ${graph_period}',
            'graph_period': 'foo',
            'graph_order': 'a b'
        }
        self.assertIsNone(self.panel.leftYAxisLabel)
        self.panel.process_graph_settings(plugin_settings)
        self.assertEqual(self.panel.leftYAxisLabel, 'vlabel foo')

    def test_process_graph_settings_default_period(self):
        plugin_settings = {
            'graph_vlabel': 'vlabel ${graph_period}',
            'graph_order': 'a b'
        }
        self.assertIsNone(self.panel.leftYAxisLabel)
        self.panel.process_graph_settings(plugin_settings)
        self.assertEqual(self.panel.leftYAxisLabel, 'vlabel second')

    @unittest.skipUnless(mock, "unittest.mock is not available.")
    def test_process_graph_thresholds_multiple_warnings(self):
        fields = {
            'foo': mock.MagicMock(settings={'warning': '10:20'}),
            'bar': mock.MagicMock(settings={'warning': '20:30'}),
        }
        result = self.panel.process_graph_thresholds(fields)
        self.assertEqual(self.panel.thresholds, {})
        self.assertEqual(result, None)

    @unittest.skipUnless(mock, "unittest.mock is not available.")
    def test_process_graph_thresholds_multiple_criticals(self):
        fields = {
            'foo': mock.MagicMock(settings={'critical': '10:20'}),
            'bar': mock.MagicMock(settings={'critical': '20:30'}),
        }
        result = self.panel.process_graph_thresholds(fields)
        self.assertEqual(self.panel.thresholds, {})
        self.assertEqual(result, None)

    @unittest.skipUnless(mock, "unittest.mock is not available.")
    def test_process_graph_thresholds_critical(self):
        fields = {
            'foo': mock.MagicMock(settings={'critical': '10:20'}),
        }
        result = self.panel.process_graph_thresholds(fields)
        self.assertEqual(self.panel.thresholds, {
            'threshold1': 20.0,  # TODO is this really the expected value?
            'threshold2': 20.0,
            'thresholdLine': False
        })
        self.assertEqual(result, None)

    @unittest.skipUnless(mock, "unittest.mock is not available.")
    def test_process_graph_thresholds_warning(self):
        fields = {
            'bar': mock.MagicMock(settings={'warning': '20:30'}),
        }
        result = self.panel.process_graph_thresholds(fields)
        self.assertEqual(self.panel.thresholds, {
            'threshold1': 30.0,
            'thresholdLine': False
        })
        self.assertEqual(result, None)

    @unittest.skipUnless(mock, "unittest.mock is not available.")
    def test_process_graph_types_stack(self):
        fields = {
            'baz': mock.MagicMock(settings={'draw': 'STACK'}),
        }
        result = self.panel.process_graph_types(fields)
        self.assertTrue(self.panel.stack)
        self.assertEqual(self.panel.linewidth, DEFAULT_LINE_WIDTH)
        self.assertEqual(self.panel.fill, 0)
        self.assertEqual(self.panel.overrides, [])
        self.assertEqual(self.panel.alias_colors, {})
        self.assertIsNone(result)

    @unittest.skipUnless(mock, "unittest.mock is not available.")
    def test_process_graph_types_area(self):
        fields = {
            'bar': mock.MagicMock(settings={'draw': 'AREA'}),
        }
        result = self.panel.process_graph_types(fields)
        self.assertFalse(self.panel.stack)
        self.assertEqual(self.panel.fill, DEFAULT_FILL)
        self.assertEqual(self.panel.linewidth, 0)
        self.assertEqual(self.panel.overrides, [])
        self.assertEqual(self.panel.alias_colors, {})
        self.assertIsNone(result)

    @unittest.skipUnless(mock, "unittest.mock is not available.")
    def test_process_graph_types_line_area(self):
        fields = {
            'foo': mock.MagicMock(settings={'draw': 'LINEAREA'}),
        }
        result = self.panel.process_graph_types(fields)
        self.assertFalse(self.panel.stack)
        self.assertEqual(self.panel.fill, DEFAULT_FILL)
        self.assertEqual(self.panel.linewidth, 0)
        self.assertEqual(self.panel.overrides, [{
            'alias': 'foo',
            'fill': 0  # Is this really the expected value?
        }])
        self.assertEqual(self.panel.alias_colors, {})
        self.assertIsNone(result)

    @unittest.skipUnless(mock, "unittest.mock is not available.")
    def test_process_graph_types_default(self):
        fields = {
            'foo': mock.MagicMock(settings={}),
        }
        result = self.panel.process_graph_types(fields)
        self.assertFalse(self.panel.stack)
        self.assertEqual(self.panel.fill, 0)
        self.assertEqual(self.panel.linewidth, DEFAULT_LINE_WIDTH)
        self.assertEqual(self.panel.overrides, [])
        self.assertEqual(self.panel.alias_colors, {})
        self.assertIsNone(result)

    @unittest.skipUnless(mock, "unittest.mock is not available.")
    def test_process_graph_types_line(self):
        fields = {
            'foo': mock.MagicMock(settings={'draw': 'LINE'}),
        }
        result = self.panel.process_graph_types(fields)
        self.assertFalse(self.panel.stack)
        self.assertEqual(self.panel.fill, 0)
        self.assertEqual(self.panel.linewidth, DEFAULT_LINE_WIDTH)
        self.assertEqual(self.panel.overrides, [])
        self.assertEqual(self.panel.alias_colors, {})
        self.assertIsNone(result)

    @unittest.skipUnless(mock, "unittest.mock is not available.")
    def test_process_graph_types_linestack(self):
        fields = {
            'foo': mock.MagicMock(settings={'draw': 'LINESTACK'}),
        }
        result = self.panel.process_graph_types(fields)
        self.assertTrue(self.panel.stack)
        self.assertEqual(self.panel.fill, 0)
        self.assertEqual(self.panel.linewidth, DEFAULT_LINE_WIDTH)
        self.assertEqual(self.panel.overrides, [])
        self.assertEqual(self.panel.alias_colors, {})
        self.assertIsNone(result)

    @unittest.skipUnless(mock, "unittest.mock is not available.")
    def test_process_graph_types_colours(self):
        fields = {
            'foo': mock.MagicMock(settings={'colour': '123456'}),
        }
        result = self.panel.process_graph_types(fields)
        self.assertFalse(self.panel.stack)
        self.assertEqual(self.panel.fill, 0)
        self.assertEqual(self.panel.linewidth, DEFAULT_LINE_WIDTH)
        self.assertEqual(self.panel.overrides, [])
        self.assertEqual(self.panel.alias_colors, {
            'foo': '#123456'
        })
        self.assertIsNone(result)

    @unittest.skipUnless(mock, "unittest.mock is not available.")
    def test_to_json(self):
        mock_settings = mock.MagicMock()
        mock_settings.influxdb = {
            'database': 'the-database'
        }
        mock_settings.grafana = {
            'show_minmax': True,
        }
        # Add a dummy query so we get a value to check against below
        query = mock.MagicMock()
        query.to_json.return_value = {'1': '2'}
        self.panel.queries = [query]

        expected = {
            'aliasColors': {},
            'datasource': 'the-database',
            'fill': 0,
            'grid': {},
            'leftYAxisLabel': None,
            'legend': {'alignAsTable': True,
                       'avg': True,
                       'current': True,
                       'max': True,
                       'min': True,
                       'rightSide': False,
                       'show': True,
                       'total': False,
                       'values': True},
            'linewidth': 1,
            'seriesOverrides': [],
            'span': 6,
            'stack': False,
            'targets': [{'1': '2'}],  # from the dummy query above
            'title': 'Hello',
            'tooltip': {'shared': False, 'value_type': 'individual'},
            'type': 'graph',
            'xaxis': {'show': True},
            'yaxes': [{'format': 'short', 'label': None, 'logBase': 1},
                      {'format': 'short', 'label': None, 'logBase': 1}]}

        result = self.panel.to_json(mock_settings)

        self.assertEqual(result, expected)


class TestHeaderPanel(unittest.TestCase):

    def setUp(self):
        self.panel = gf.HeaderPanel(title="Hello")

    def test_to_json(self):
        expected = {
            "title": "Hello",
            "mode": "html",
            "type": "text",
            "editable": True,
            "span": 12,
            "links": [{
                "type": "absolute",
                "title": "Fork me on GitHub!",
                "url": "https://github.com/mvonthron/munin-influxdb",
            }],
            "content": ""
        }

        result = self.panel.to_json(None)

        self.assertEqual(result, expected)


class TestRow(unittest.TestCase):

    def test_add_panel(self):
        row = gf.Row('Hello')
        self.assertEqual(row.panels, [])
        result = row.add_panel()
        self.assertEqual(len(row.panels), 1)
        self.assertIsInstance(result, gf.Panel)

    def test_to_json(self):
        row = gf.Row('Hello')
        result = row.to_json(None)
        expected = {
            "title": 'Hello',
            "height": '250px',
            "panels": [],
            "showTitle": True
        }
        self.assertEqual(result, expected)
