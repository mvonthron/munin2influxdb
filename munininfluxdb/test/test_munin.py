from io import StringIO
from textwrap import dedent
import unittest

from munininfluxdb.munin import (
    cleanup,
    generate_filenames,
    populate_settings,
)
from munininfluxdb.settings import Settings

from . import mock


EXAMPLE_DATA = StringIO(dedent(
    u'''\
    version 2.0.19-3
    group1;top.level.domain:postgres_locks_dbname.accesssharelock.type GAUGE
    group1;top.level.domain:postgres_connections_db.template1.graph_data_size normal
    group1;top.level.domain:cpu.system.info CPU time spent by the kernel in system activities
    group1;top.level.domain:cpu.irq.graph_data_size normal
    group1;top.level.domain:apache_volume.volume80.label port 80
    group1;top.level.domain:df.graph_vlabel %
    group1;top.level.domain:df.graph_title Disk usage in percent
    group1;top.level.domain:apache_volume.volume80.type DERIVE
    group2;mailserver:memory.mapped.update_rate 300
    group2;mailserver:postfix_mailstats.delivered.label No .label provided
    group2;mailserver:postfix_mailstats.delivered.update_rate 300
    group2;mailserver:postfix_mailstats.delivered.extinfo NOTE: The plugin did not provide any label for the data source delivered.  It is in need of fixing.
    group2;mailserver:postfix_mailstats.delivered.graph_data_size normal
    group3;blackdragon.fritz.box:homematic_radiator_kummer_temperature.graph_category homematic
    group3;blackdragon.fritz.box:homematic_radiator_kummer_temperature.graph_title Heizung Kummer temp
    group3;blackdragon.fritz.box:homematic_radiator_kummer_temperature.graph_vlabel temp
    group3;blackdragon.fritz.box:homematic_radiator_kummer_temperature.graph_printf %3.0lf
    group3;blackdragon.fritz.box:homematic_radiator_kummer_temperature.graph_args --base 1000 --lower-limit -10 --upper-limit 45
    group3;blackdragon.fritz.box:homematic_radiator_kummer_temperature.a.value 10
    '''))


class TestDataFileHandling(unittest.TestCase):

    def setUp(self):
        EXAMPLE_DATA.seek(0)

    def test_read_state_file(self):
        self.skipTest("I don't know what the method "
                      "read_state_file is supposed to do.")  # TODO

    def test_populate_settings_from_www(self):
        self.skipTest('I have no exmaple HTML file at hand right now')  # TODO

    def test_populate_settings_from_datafile(self):
        expected_groups = {'group1', 'group2', 'group3'}
        expected_domains = {
            'top.level.domain', 'mailserver', 'blackdragon.fritz.box'}
        expected_fields = {
            'a',
            'delivered',
            'template1',
            'irq',
            'system',
            'accesssharelock',
            'volume80',
            'mapped'
        }
        expected_plugins = {
            'postgres_locks_dbname',
            'cpu',
            'apache_volume',
            'postgres_connections_db',
            'homematic_radiator_kummer_temperature',
            'postfix_mailstats',
            'memory',
        }

        settings = Settings()

        self.assertEqual(settings.domains.keys(), [])

        populate_settings(settings, EXAMPLE_DATA)

        self.assertEqual(set(settings.domains.keys()),
                         {'group1', 'group2', 'group3'})

        plugins = {_[-1] for _ in settings.iter_plugins()}
        self.assertEqual(plugins, expected_plugins)

        groups = set()
        domains = set()
        plugins = set()
        fields = set()
        for group, domain, plugin, field in settings.iter_fields():
            groups.add(group)
            domains.add(domain)
            plugins.add(plugin)
            fields.add(field)

        self.assertEqual(groups, expected_groups)
        self.assertEqual(domains, expected_domains)
        self.assertEqual(plugins, expected_plugins)
        self.assertEqual(fields, expected_fields)

    def test_generate_filename(self):
        settings = Settings()
        populate_settings(settings, EXAMPLE_DATA)
        generate_filenames(settings)

        expected_rrd_filenames = {
            '/var/lib/munin/group1/top.level.domain-postgres_locks_dbname-accesssharelock-g.rrd',
            '/var/lib/munin/group1/top.level.domain-cpu-irq-g.rrd',
            '/var/lib/munin/group1/top.level.domain-cpu-system-g.rrd',
            '/var/lib/munin/group1/top.level.domain-apache_volume-volume80-d.rrd',
            '/var/lib/munin/group1/top.level.domain-postgres_connections_db-template1-g.rrd',
            '/var/lib/munin/group3/blackdragon.fritz.box-homematic_radiator_kummer_temperature-a-g.rrd',
            '/var/lib/munin/group2/mailserver-postfix_mailstats-delivered-g.rrd',
            '/var/lib/munin/group2/mailserver-memory-mapped-g.rrd',
        }

        expected_xml_filenames = {
            '/tmp/munin-influxdb/xml/group2-mailserver-memory-mapped-g.xml',
            '/tmp/munin-influxdb/xml/group2-mailserver-postfix_mailstats-delivered-g.xml',
            '/tmp/munin-influxdb/xml/group3-blackdragon.fritz.box-homematic_radiator_kummer_temperature-a-g.xml',
            '/tmp/munin-influxdb/xml/group1-top.level.domain-postgres_connections_db-template1-g.xml',
            '/tmp/munin-influxdb/xml/group1-top.level.domain-apache_volume-volume80-d.xml',
            '/tmp/munin-influxdb/xml/group1-top.level.domain-cpu-system-g.xml',
            '/tmp/munin-influxdb/xml/group1-top.level.domain-cpu-irq-g.xml',
            '/tmp/munin-influxdb/xml/group1-top.level.domain-postgres_locks_dbname-accesssharelock-g.xml',
        }

        rrd_filenames = set()
        xml_filenames = set()
        for domain, host, plugin, field in settings.iter_fields():
            _field = settings.domains[domain].hosts[host].plugins[plugin].fields[field]
            rrd_filenames.add(_field.rrd_filename)
            xml_filenames.add(_field.xml_filename)

        self.assertEqual(expected_xml_filenames, xml_filenames)
        self.assertEqual(expected_rrd_filenames, rrd_filenames)

    def test_cleanup(self):
        plugins = {
            'mg_plugin1': mock.MagicMock(
                fields={
                    'mg_field1': [1, 2, 3]
                }
            ),
            'mg_plugin2': mock.MagicMock(
                fields={
                    'mg_field2': [4, 5, 6]
                }
            )
        }
        mock_settings = mock.MagicMock(
            domains={
                'domain': mock.MagicMock(
                    hosts={
                        'host': mock.MagicMock(
                            plugins=plugins
                        )
                    }
                )
            }
        )
        mock_settings.iter_fields.return_value = [
            ('domain', 'host', 'mg_plugin1.mg_field1', 'field1'),
            ('domain', 'host', 'mg_plugin2.mg_field2', 'field2'),
        ]

        self.assertTrue('mg_field1' in plugins['mg_plugin1'].fields)
        self.assertTrue('mg_field2' in plugins['mg_plugin2'].fields)
        cleanup(mock_settings)
        self.assertFalse('mg_field1' in plugins['mg_plugin1'].fields)
        self.assertFalse('mg_field2' in plugins['mg_plugin2'].fields)
