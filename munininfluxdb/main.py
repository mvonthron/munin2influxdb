from __future__ import print_function
from argparse import ArgumentParser
import sys

from munininfluxdb.utils import Symbol
import munininfluxdb.commands.cron as cmd_cron
import munininfluxdb.commands.dump as cmd_dump
import munininfluxdb.commands.fetch as cmd_fetch
import munininfluxdb.commands.import_ as cmd_import
import munininfluxdb.external.cron as cron


def main():
    parser = ArgumentParser(description='TODO')  # TODO
    parser.add_argument('--interactive', dest='interactive', action='store_true')
    parser.add_argument('--no-interactive', dest='interactive', action='store_false')
    parser.set_defaults(interactive=True)

    subparsers = parser.add_subparsers(
        title='subcommands',
        description='valid subcommands',
        help='additional help'
    )

    for subcommand in (cmd_import, cmd_fetch, cmd_cron, cmd_dump):
        subparser = subparsers.add_parser(subcommand.NAME,
                                          description=subcommand.DESCRIPTION)
        subcommand.setup(subparser, {
            'cron': cron
        })

    args = parser.parse_args()
    try:
        args.func(args)
    except KeyboardInterrupt:
        print("\n{0} Canceled.".format(Symbol.NOK_RED))
        sys.exit(1)
    except Exception as e:
        raise
        print("{0} Error: {1}".format(Symbol.NOK_RED, e))
        sys.exit(1)
