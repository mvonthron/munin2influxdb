from __future__ import print_function
import os
import pwd
import sys

from munininfluxdb.utils import Symbol, absolute_executable


# Cron job comment is used to uninstall and must not be manually deleted from the crontab
CRON_COMMENT = 'Update InfluxDB with fresh values from Munin'
NAME = 'cron'
DESCRIPTION = 'Installs or uninstalls the CRON job'


def get_cron_user():
    try:
        pwd.getpwnam('munin')
    except KeyError:
        output = 'root'
    else:
        output = 'munin'
    return output


def uninstall_cron(cron_adapter):
    """
    Creates a function which uses *cron_adapter* to remove an entry from the
    CRONtab.

    See :py:mod:`munininfluxdb.external.cron` for an example of an adapter.
    """
    def fun(args):
        """
        Main function for the "cron uninstall" command.

        :param args: The result from parsing CLI arguments.
        """
        if os.geteuid() != 0:
            print("It seems you are not root, please run \"muninflux cron uninstall\" again with root privileges")
            sys.exit(1)

        user = args.user or get_cron_user()
        nb = cron_adapter.remove_by_comment(user, CRON_COMMENT)

        if nb:
            print("{0} Cron job uninstalled for user {1} ({2} entries deleted)".format(Symbol.OK_GREEN, user, nb))
        else:
            print("No matching job found (searching comment \"{1}\" in crontab for user {2})".format(Symbol.WARN_YELLOW,
                                                                                                 CRON_COMMENT, user))
    return fun


def install_cron(cron_adapter):
    """
    Creates a function which uses *cron_adapter* to add an entry to the CRONtab.

    See :py:mod:`munininfluxdb.external.cron` for an example of an adapter.
    """
    def fun(args):
        """
        Main function for the "cron install" command.

        :param args: The result from parsing CLI arguments.
        :return: Whether the operation was successful or not.
        :rtype: bool
        """
        script_path = absolute_executable()
        cmd = '%s fetch' % script_path

        if os.geteuid() != 0:
            print("It seems you are not root, please run \"%s cron install\" again with root privileges")
            sys.exit(1)

        user = args.user or get_cron_user()
        success = cron_adapter.add_with_comment(user, cmd, args.period, CRON_COMMENT)

        print("{0} Cron job installed for user {1}".format(Symbol.OK_GREEN, user))
        return success
    return fun


def setup(parser, injections):
    """
    Sets up CLI argument parsing.

    The argument *injections* should be a dictionary containing a key 'cron'
    mapping to a cron adapter. For an example cron adapter see
    ``munininfluxdb/external/cron.py``

    :param parser: The argument parser for this subcommand.
    :param injections: A dictionary containing the key ``'cron'`` mapping to an
        implementation of a CRON adapter. See
        :py:mod:`munininfluxdb.external.cron` for an example.
    """
    parser.add_argument('-u', '--user', default='', metavar='USER',
                        help='The CRON user')

    subparsers = parser.add_subparsers(title='CRON commands')
    install_parser = subparsers.add_parser(
        'install', description='Installs the CRON job')
    uninstall_parser = subparsers.add_parser(
        'uninstall', description='Uninstalls the CRON job')

    install_parser.add_argument(
        '-p', '--period', default=5, type=int,
        help="sets the period in minutes between each fetch in the cron job (default: %(default)dmin)")

    cron_adapter = injections['cron']
    install_parser.set_defaults(func=install_cron(cron_adapter))
    uninstall_parser.set_defaults(func=uninstall_cron(cron_adapter))
