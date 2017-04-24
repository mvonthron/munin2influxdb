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


class TestDashboard(unittest.TestCase):

    def setUp(self):
        self.mock_settings = mock.MagicMock(
            grafana={
                'auth': 'val-auth',
                'host': 'val-host',
                'access': 'val-access',
                'title': 'DBTitle',
                'tags': ['tag1', 'tag2'],
                'graph_per_row': 5,
                'show_minmax': True,
            },
            influxdb={
                'host': 'val-influxdb-host',
                'port': 1234,
                'user': 'val-influxdb-user',
                'password': 'val-influxdb-passwd',
                'database': 'dbname',
            },
            domains={
                'domain1': mock.MagicMock(
                    name='mock-domain1',
                    hosts={
                        'host1': mock.MagicMock(
                            name='mock-host1',
                            plugins={
                                'plugin1': mock.MagicMock(
                                    name='mock-plugin1',
                                    settings={'graph_title': 'Plugin1'},
                                    fields={
                                        'field1': mock.MagicMock(
                                            name='mock-field1')
                                    }
                                ),
                            }
                        )
                    }
                )
            }
        )
        self.dash = gf.Dashboard(self.mock_settings)

    def test_generate_simple(self):
        self.skipTest('Dashboard.generate_simple does not work as defined!')

    def test_prompt_setup(self):
        self.skipTest('Testing interactive prompts is cumbersome. '
                      'Skipping for now!')

    def test_add_header(self):
        mock_settings = mock.MagicMock(
            influxdb={'a': 1, 'b': 2}
        )
        self.assertEqual(len(self.dash.rows), 0)
        self.dash.add_header(mock_settings)
        self.assertEqual(len(self.dash.rows), 1)
        created_panels = self.dash.rows[0].panels
        self.assertEqual(len(created_panels), 1)
        self.assertIsInstance(created_panels[0], gf.HeaderPanel)
        self.assertEqual(created_panels[0].title,
                         'Welcome to your new dashboard!')

    def test_add_row(self):
        self.assertEqual(len(self.dash.rows), 0)
        self.dash.add_row(title="Hello World!")
        self.assertEqual(len(self.dash.rows), 1)
        self.assertIsInstance(self.dash.rows[0], gf.Row)
        self.assertEqual(self.dash.rows[0].title, 'Hello World!')

    def test_to_json(self):
        settings = mock.MagicMock()
        result = self.dash.to_json(settings)
        expected = {
            'id': None,
            'title': 'DBTitle',
            'tags': ['tag1', 'tag2'],
            'rows': [],
            'timezone': 'browser',
            'time': {'from': 'now-5d', 'to': 'now'},
        }
        settings.assert_not_called()
        self.assertEqual(result, expected)

    def test_save(self):
        from io import BytesIO
        fakefile = BytesIO()
        with mock.patch('munininfluxdb.grafana.open') as mock_open, \
                mock.patch('munininfluxdb.grafana.json') as mock_json:
            mock_open.return_value = fakefile
            expected_json_content = self.dash.to_json(None)
            self.dash.save('/tmp/foo.json')
            mock_json.dump.assert_called_with(expected_json_content, fakefile)

    def test_upload(self):
        with mock.patch('munininfluxdb.grafana.GrafanaApi') as mck_api:
            self.dash.upload()
            mck_api.assert_called_with(self.mock_settings)
            mck_api().create_datasource.assert_called_with('dbname', 'dbname')
            json_content = self.dash.to_json(None)
            mck_api().create_dashboard.assert_called_with(json_content)

    def test_generate(self):
        self.maxDiff = None

        self.assertEqual(self.dash.rows, [])

        self.dash.generate()

        self.assertEqual(len(self.dash.rows), 2)  # Panel + 1 Plugin
        row_1, row_2 = self.dash.rows
        self.assertIsInstance(row_1.panels[0], gf.HeaderPanel)

        self.assertEqual(len(row_1.panels), 1)
        expected = {
            'aliasColors': {},
            'datasource': 'dbname',
            'fill': 0,
            'grid': {},
            'leftYAxisLabel': None,
            'legend': {
                'alignAsTable': True,
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
            'span': 2,
            'stack': False,
            'targets': [{
                'alias': 'field1',
                'dsType': 'influxdb',
                'groupBy': [{'params': ['$interval'], 'type': 'time'},
                            {'params': ['null'], 'type': 'fill'}],
                'measurement': 'plugin1',
                'resultFormat': 'time_series',
                'select': [[{'params': ['field1'], 'type': 'field'},
                            {'params': [], 'type': 'mean'}]]
            }],
            'title': 'Plugin1',
            'tooltip': {'shared': False, 'value_type': 'individual'},
            'type': 'graph',
            'xaxis': {'show': True},
            'yaxes': [{'format': 'short', 'label': None, 'logBase': 1},
                      {'format': 'short', 'label': None, 'logBase': 1}]}
        result_json = row_2.panels[0].to_json(self.mock_settings)
        self.assertEqual(result_json, expected)


@unittest.skipUnless(mock, "unittest.mock is not available.")
class TestGrafanaAPI(unittest.TestCase):

    def setUp(self):
        self.requests_patcher = mock.patch('munininfluxdb.grafana.requests')
        self.__requests = self.requests_patcher.start()

    def tearDown(self):
        self.requests_patcher.stop()

    def test_test_host(self):
        self.__requests.get.return_value = mock.MagicMock(status_code=401)
        result = gf.GrafanaApi.test_host('foo')
        self.assertTrue(result)
        self.__requests.get.assert_called_with('foo/api/org')

    def test_test_auth(self):
        self.__requests.get.return_value = mock.MagicMock(status_code=200)
        result = gf.GrafanaApi.test_auth('foo', 'auth')
        self.assertTrue(result)
        self.__requests.get.assert_called_with('foo/api/org', auth='auth')

    def test_create_datasource(self):
        mock_settings = mock.MagicMock(
            grafana={
                'auth': 'val-auth',
                'host': 'val-host',
                'access': 'val-access',
            },
            influxdb={
                'host': 'val-influxdb-host',
                'port': 1234,
                'user': 'val-influxdb-user',
                'password': 'val-influxdb-passwd',
            }
        )

        expected_payload = {
            "name": "dsname",
            "database": "dbname",
            "type": "influxdb",
            "url": "http://val-influxdb-host:1234",
            "user": "val-influxdb-user",
            "password": "val-influxdb-passwd",
            "access": "val-access",
            "basicAuth": False
        }

        self.__requests.post.return_value = mock.MagicMock(ok=True)

        api = gf.GrafanaApi(mock_settings)
        result = api.create_datasource('dsname', 'dbname')

        self.__requests.post.assert_called_with(
            'val-host/api/datasources',
            auth='val-auth',
            json=expected_payload
        )

        self.assertTrue(result)

    def test_create_dashboard(self):

        mock_settings = mock.MagicMock(
            grafana={
                'auth': 'val-auth',
                'host': 'val-host',
            },
        )

        mock_response = mock.MagicMock(ok=True)
        mock_response.json.return_value = {'slug': 'val-slug'}
        self.__requests.post.return_value = mock_response

        request_data = {'dashboard': {'foo': 'bar'}}

        api = gf.GrafanaApi(mock_settings)
        result = api.create_dashboard({'foo': 'bar'})

        self.__requests.post.assert_called_with(
            'val-host/api/dashboards/db',
            auth='val-auth',
            json=request_data)

        self.assertEqual(result, 'val-host/dashboard/db/val-slug')
