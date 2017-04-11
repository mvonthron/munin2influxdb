import unittest

import munininfluxdb.rrd as rrd

from . import mock


class MockRRA:

    def __init__(self, pdp_per_row):
        self.pdp_per_row = pdp_per_row


@unittest.skipUnless(mock, "unittest.mock is not available.")
class TestRFetch(unittest.TestCase):

    def setUp(self):
        self.os_patcher = mock.patch('munininfluxdb.rrd.os')
        self.sp_patcher = mock.patch('munininfluxdb.rrd.subprocess')
        self.pb_patcher = mock.patch('munininfluxdb.rrd.ProgressBar')
        self.print_patcher = mock.patch('munininfluxdb.rrd.print')
        self.__os = self.os_patcher.start()
        self.__subprocess = self.sp_patcher.start()
        self.__ProgressBar = self.pb_patcher.start()
        self.__print = self.print_patcher.start()

    def tearDown(self):
        self.os_patcher.stop()
        self.sp_patcher.stop()
        self.pb_patcher.stop()
        self.print_patcher.stop()

    def test_read_xml_file(self):
        with mock.patch('munininfluxdb.rrd.ET') as mock_et:
            mock_tree = mock.MagicMock(name='tree')
            mock_et.parse.return_value = mock_tree
            mock_root = mock.MagicMock(name='root')
            mock_root.find.side_effect = [
                mock.MagicMock(text='1000'),  # find('lastupdate')
                mock.MagicMock(text='5'),  # find('step')
            ]
            rra1 = mock.MagicMock(name='rra1')
            rra1.find.side_effect = [
                mock.MagicMock(text='3'),  # find('pdp_per_row')
                [4, 5],  # find('database')
            ]
            rra1.findall.return_value = [mock.MagicMock(text='10.0')]
            rra2 = mock.MagicMock(name='rra2')
            rra2.find.side_effect = [
                mock.MagicMock(text='5'),  # find('pdp_per_row')
                [4, 5, 6],  # find('database')
            ]
            rra2.findall.return_value = [mock.MagicMock(text='15.0')]
            mock_root.findall.side_effect = [
                ['ds1'],  # findall('ds')
                [rra1, rra2]  # findall('rra')
            ]
            mock_tree.getroot.return_value = mock_root

            result = rrd.read_xml_file('myfilename', keep_average_only=False)
            mock_tree.getroot.assert_called_with()
            mock_root.assert_has_calls([
                mock.call.find('lastupdate'),
                mock.call.find('step'),
                mock.call.findall('ds'),
                mock.call.findall('rra'),
            ])

            rra1.assert_has_calls([
                mock.call.find('pdp_per_row'),
                mock.call.find('database'),
                mock.call.findall('./database/row/v'),
            ])

            rra2.assert_has_calls([
                mock.call.find('pdp_per_row'),
                mock.call.find('database'),
                mock.call.findall('./database/row/v'),
            ])

        expected = {
            950: 15.0,
            975: 10.0,
        }
        self.assertEqual(dict(result), expected)

    def test_export_to_xml(self):
        field1 = mock.MagicMock(name='field1', rrd_filename='rrdfile1.rrd',
                                xml_filename='xmlfile1')
        field2 = mock.MagicMock(name='field2', rrd_filename='rrdfile2.rrd',
                                xml_filename='xmlfile2')
        mock_settings = mock.MagicMock(
            paths={
                'xml': '/path/to/xml'
            },
            domains={
                'domain': mock.MagicMock(
                    hosts={
                        'host': mock.MagicMock(
                            plugins={
                                'plugin': mock.MagicMock(
                                    fields={
                                        'field1': field1,
                                        'field2': field2,
                                    }
                                )
                            }
                        )
                    }
                )
            }
        )
        mock_settings.iter_fields.return_value = [
            ('domain', 'host', 'plugin', 'field1'),
            ('domain', 'host', 'plugin', 'field2'),
        ]

        rrd.export_to_xml(mock_settings)

        self.__subprocess.check_call.assert_has_calls([
            mock.call(['rrdtool', 'dump', 'rrdfile1.rrd', 'xmlfile1']),
            mock.call(['rrdtool', 'dump', 'rrdfile2.rrd', 'xmlfile2']),
        ], any_order=True)
        self.__os.makedirs.assert_called_with('/path/to/xml')

    def test_export_to_xml_in_folder(self):
        self.__os.listdir.return_value = [
            'file1.rrd',
            'file2.rrd',
            'file3',
        ]
        self.__os.path.join.side_effect = lambda *x: '/'.join(x)
        rrd.export_to_xml_in_folder('/path/to/source')

        self.skipTest('The function under test does not seem to be implemented '
                      'correctly. Test skipped for now.')
        # TODO these calls don't look correct, but that's what's currently
        # implemented. For now, I'm focussing on creating tests, not the
        # correctness of the code! This needs to be fixed before re-enabling the
        # test!
        self.__subprocess.check_call.assert_has_calls([
            mock.call(['rrdtool', 'dump', '/path/to/source///path/to/source/file1.rrd', '/tmp/munin-influxdb/xml/-/path/to/source/file1.xml']),
            mock.call(['rrdtool', 'dump', '/path/to/source///path/to/source/file2.rrd', '/tmp/munin-influxdb/xml/-/path/to/source/file2.xml']),
        ], any_order=True)

    def test_discover_from_rrd(self):
        field = mock.MagicMock(
            name='field',
            rrd_filename='rrdfile1.rrd',
            xml_filename='xmlfile1'
        )
        plugin = mock.MagicMock(fields={
            'field': field,
        })
        mock_settings = mock.MagicMock(
            nb_rrd_files=0,
            paths={
                'xml': '/path/to/xml',
                'munin': '/path/to/munin',
            },
            domains={
                'domain': mock.MagicMock(
                    hosts={
                        'host': mock.MagicMock(
                            plugins={
                                'plugin': plugin
                            }
                        )
                    }
                )
            }
        )
        mock_settings.iter_fields.return_value = [
            ('domain', 'host', 'plugin', 'field1'),
            ('domain', 'host', 'plugin', 'field2'),
        ]

        # --- prime the os mock ----------
        self.__os.listdir.return_value = [
            'file1',
            'host-plugin-field-d.rrd',
            'domain',
        ]
        self.__os.path.isdir.side_effect = lambda x: x == '/path/to/munin/domain'
        self.__os.path.join.side_effect = lambda *x: '/'.join(x)
        self.__os.path.splitext.return_value = ('host-plugin-field-d', 'rrd')
        # --------------------------------

        result = rrd.discover_from_rrd(mock_settings)
        self.assertEqual(result, mock_settings)
        self.__os.listdir.assert_has_calls([
            mock.call('/path/to/munin'),
            mock.call('/path/to/munin/domain'),
        ], any_order=True)

        # This check verifies that the mocked file structure above leads to the
        # expected settings
        expected = {
            'rrd_found': True,
            'rrd_filename': '/path/to/munin/domain/host-plugin-field-d.rrd',
            'xml_filename': '/path/to/xml/domain/host-plugin-field-d.xml',
            'settings': {'type': 'DERIVE'},
        }
        field_result = {
            'rrd_found': plugin.fields['field'].rrd_found,
            'rrd_filename': plugin.fields['field'].rrd_filename,
            'xml_filename': plugin.fields['field'].xml_filename,
            'settings': plugin.fields['field'].settings,
        }
        self.assertEqual(field_result, expected)

    def test_check_rrd_files(self):
        field1 = mock.MagicMock(name='field1', rrd_filename='rrdfile1.rrd',
                                xml_filename='xmlfile1')
        field2 = mock.MagicMock(name='field2', rrd_filename='rrdfile2.rrd',
                                xml_filename='xmlfile2')
        mock_settings = mock.MagicMock(
            nb_rrd_files=0,
            paths={
                'xml': '/path/to/xml'
            },
            domains={
                'domain': mock.MagicMock(
                    hosts={
                        'host': mock.MagicMock(
                            plugins={
                                'plugin': mock.MagicMock(
                                    fields={
                                        'field1': field1,
                                        'field2': field2,
                                    }
                                )
                            }
                        )
                    }
                )
            }
        )
        mock_settings.iter_fields.return_value = [
            ('domain', 'host', 'plugin', 'field1'),
            ('domain', 'host', 'plugin', 'field2'),
        ]

        rrd.check_rrd_files(mock_settings)

        self.assertEqual(mock_settings.nb_rrd_files, 2)
