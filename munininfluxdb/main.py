from __future__ import print_function
from argparse import ArgumentParser
import sys

from munininfluxdb.utils import Symbol
import munininfluxdb.commands.cron as cmd_cron
import munininfluxdb.commands.dump as cmd_dump
import munininfluxdb.commands.fetch as cmd_fetch
import munininfluxdb.commands.import_ as cmd_import
import munininfluxdb.external.cron as cron


def dummy_function(args):
    """
    Dummy function which is called if no subcommand was loaded.


    Developer Note:

        This exists mainly that so that we can mock it during unit-tests and
        check that the submodule function is called properly without actually
        calling any subcommand.
    """
    print('Dummy function. If you see this, no subcommand was loaded. '
          'It is HIGHLY unlikely that you see this! '
          'If you do, please contact the developers!')
    return 0


def main(args=None, commands=None):
    # Allow some unit-tetst injections
    args = args or sys.argv[1:]
    if not commands:
        commands = {
            'cron': cmd_cron,
            'dump': cmd_dump,
            'fetch': cmd_fetch,
            'import': cmd_import,
        }

    # Prepare the CLI parser
    parser = ArgumentParser(description='TODO')  # TODO
    parser.add_argument('--interactive', dest='interactive', action='store_true')
    parser.add_argument('--no-interactive', dest='interactive', action='store_false')
    parser.set_defaults(interactive=True)
    parser.set_defaults(func=dummy_function)

    subparsers = parser.add_subparsers(
        title='subcommands',
        description='valid subcommands',
        help='additional help'
    )

    # Initialise CLI argument parser for the subcommands
    for subcommand in commands.values():
        subparser = subparsers.add_parser(subcommand.NAME,
                                          description=subcommand.DESCRIPTION)
        subcommand.setup(subparser, {
            'cron': cron
        })

    # Parse the arguments and execute the command
    namespace = parser.parse_args(args)
    try:
        namespace.func(namespace)
    except KeyboardInterrupt:
        print("\n{0} Canceled.".format(Symbol.NOK_RED))
        return 1
    except Exception as e:
        print("{0} Error: {1}".format(Symbol.NOK_RED, e))
        return 1
    return 0
