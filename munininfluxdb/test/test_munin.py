from io import StringIO
from textwrap import dedent
import unittest

from munininfluxdb.munin import populate_settings
from munininfluxdb.settings import Settings


class TestDataFileHandling(unittest.TestCase):

    def test_populate_settings(self):
        data = StringIO(dedent(
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

        populate_settings(settings, data)

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
