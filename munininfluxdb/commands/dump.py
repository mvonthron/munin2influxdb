import logging

from munininfluxdb import munin
from munininfluxdb import rrd
from munininfluxdb.settings import Settings, Defaults
from munininfluxdb.utils import Symbol


LOG = logging.getLogger(__name__)
NAME = 'dump'
DESCRIPTION = """
The 'dump' command writes out the munin RRD files to XML. These XML files can
then be used by the 'load' command to import them into influxdb.
"""


def retrieve_munin_configuration(settings):
    """
    """
    print("Exploring Munin structure")

    try:
        settings = munin.discover_from_datafile(settings)
    except Exception as e:
        LOG.debug('Traceback:', exc_info=True)
        print("  {0} Could not process datafile ({1}), will read www and RRD cache instead".format(Symbol.NOK_RED, settings.paths['datafile']))

        # read /var/cache/munin/www to check what's currently displayed on the dashboard
        settings = munin.discover_from_www(settings)
        settings = rrd.discover_from_rrd(settings, insert_missing=False)
    else:
        print("  {0} Found {1}: extracted {2} measurement units".format(Symbol.OK_GREEN, settings.paths['datafile'],
                                                                        settings.nb_fields))

    # for each host, find the /var/lib/munin/<host> directory and check if node name and plugin conf match RRD files
    try:
        rrd.check_rrd_files(settings)
    except Exception as e:
        print("  {0} {1}".format(Symbol.NOK_RED, e))
    else:
        print("  {0} Found {1} RRD files".format(Symbol.OK_GREEN, settings.nb_rrd_files))

    return settings


def main(args):
    settings = Settings(args)
    settings = retrieve_munin_configuration(settings)

    # export RRD files as XML for (much) easier parsing (but takes much more time)
    print("\nExporting RRD databases:".format(settings.nb_rrd_files))
    nb_xml = rrd.export_to_xml(settings)
    print("  {0} Exported {1} RRD files to XML ({2})".format(Symbol.OK_GREEN, nb_xml, settings.paths['xml']))


def setup(parser, injections):
    """
    Sets up CLI argument parsing.

    The argument *injections* is currently unused in this command and is a
    placeholder for the future.

    :param parser: The argument parser for this subcommand.
    """
    parser.add_argument('--xml-temp-path', default=Defaults.MUNIN_XML_FOLDER,
                        help='set path where to store result of RRD exported files (default: %(default)s)')
    parser.add_argument('--keep-temp', action='store_true',
                        help='instruct to retain temporary files (mostly RRD\'s XML) after generation')
    parser.add_argument('-v', '--verbose', type=int, default=1,
                        help='set verbosity level (0: quiet, 1: default, 2: debug)')

    # Munin
    munargs = parser.add_argument_group('Munin parameters')
    munargs.add_argument('--munin-path', default=Defaults.MUNIN_VAR_FOLDER,
                         help='path to main Munin folder (default: %(default)s)')
    munargs.add_argument('--www', '--munin-www-path', default=Defaults.MUNIN_WWW_FOLDER,
                         help='path to main Munin folder (default: %(default)s)')
    munargs.add_argument('--rrd', '--munin-rrd-path', default=Defaults.MUNIN_RRD_FOLDER,
                         help='path to main Munin folder (default: %(default)s)')
    parser.set_defaults(func=main)
