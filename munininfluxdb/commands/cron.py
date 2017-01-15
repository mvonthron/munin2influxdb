from __future__ import print_function
import os
import pwd
import sys

from munininfluxdb.utils import Symbol, absolute_executable


try:
    pwd.getpwnam('munin')
except KeyError:
    CRON_USER = 'root'
else:
    CRON_USER = 'munin'

# Cron job comment is used to uninstall and must not be manually deleted from the crontab
CRON_COMMENT = 'Update InfluxDB with fresh values from Munin'
NAME = 'cron'
DESCRIPTION = 'Installs or uninstalls the CRON job'


def uninstall_cron():
    if os.geteuid() != 0:
        print("It seems you are not root, please run \"muninflux fetch --uninstall-cron\" again with root privileges")
        sys.exit(1)

    try:
        import crontab
    except ImportError:
        from vendor import crontab

    cron = crontab.CronTab(user=CRON_USER)
    jobs = list(cron.find_comment(CRON_COMMENT))
    cron.remove(*jobs)
    cron.write()

    return len(jobs)


def install_cron(script_file, period):
    if os.geteuid() != 0:
        print("It seems you are not root, please run \"muninflux fetch --install-cron\" again with root privileges")
        sys.exit(1)

    try:
        import crontab
    except ImportError:
        from vendor import crontab

    cron = crontab.CronTab(user=CRON_USER)
    job = cron.new(command=script_file, user=CRON_USER, comment=CRON_COMMENT)
    job.minute.every(period)

    if job.is_valid() and job.is_enabled():
        cron.write()

    return job.is_valid() and job.is_enabled()


def setup(parser):
    parser.add_argument('script_path',
                        help='install a cron job to updated InfluxDB with fresh data from Munin every <period> minutes')
    parser.add_argument('-p', '--period', default=5, type=int,
                        help="sets the period in minutes between each fetch in the cron job (default: %(default)dmin)")
    parser.add_argument('--uninstall-cron', action='store_true',
                        help='uninstall the fetch cron job (any matching the initial comment actually)')
    parser.set_defaults(func=main)


def main(args):
    print(absolute_executable())
    raise NotImplementedError('Not yet implemented as subcommand')
    # TODO from pkg_resources import load_entry_point
    # TODO entry = load_entry_point('munin-influxdb', 'console_scripts', 'muninflux_fetch')
    # TODO # python bin/fetch.py --install-cron $(dirname $(readlink -f "$0"))/bin/fetch.py

    if args.script_path:
        install_cron(args.script_path, args.period)
        print("{0} Cron job installed for user {1}".format(Symbol.OK_GREEN, CRON_USER))
        return
    elif args.uninstall_cron:
        nb = uninstall_cron()
        if nb:
            print("{0} Cron job uninstalled for user {1} ({2} entries deleted)".format(Symbol.OK_GREEN, CRON_USER, nb))
        else:
            print("No matching job found (searching comment \"{1}\" in crontab for user {2})".format(Symbol.WARN_YELLOW,
                                                                                                     CRON_COMMENT, CRON_USER))
        return
