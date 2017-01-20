from __future__ import print_function
import os
import pwd
import sys

import crontab

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


def uninstall_cron(args):
    if os.geteuid() != 0:
        print("It seems you are not root, please run \"muninflux fetch --uninstall-cron\" again with root privileges")
        sys.exit(1)

    cron = crontab.CronTab(user=CRON_USER)
    jobs = list(cron.find_comment(CRON_COMMENT))
    cron.remove(*jobs)
    cron.write()

    nb = len(jobs)
    if nb:
        print("{0} Cron job uninstalled for user {1} ({2} entries deleted)".format(Symbol.OK_GREEN, CRON_USER, nb))
    else:
        print("No matching job found (searching comment \"{1}\" in crontab for user {2})".format(Symbol.WARN_YELLOW,
                                                                                                 CRON_COMMENT, CRON_USER))


def install_cron(args):
    script_path = absolute_executable()
    cmd = '%s fetch' % script_path

    if os.geteuid() != 0:
        print("It seems you are not root, please run \"%s cron install\" again with root privileges")
        sys.exit(1)

    cron = crontab.CronTab(user=CRON_USER)
    job = cron.new(command=cmd, user=CRON_USER, comment=CRON_COMMENT)
    job.minute.every(args.period)

    if job.is_valid() and job.is_enabled():
        cron.write()

    print("{0} Cron job installed for user {1}".format(Symbol.OK_GREEN, CRON_USER))
    return job.is_valid() and job.is_enabled()


def setup(parser):
    subparsers = parser.add_subparsers(title='CRON commands')
    install_parser = subparsers.add_parser(
        'install', description='Installs the CRON job')
    uninstall_parser = subparsers.add_parser(
        'uninstall', description='Uninstalls the CRON job')

    install_parser.add_argument(
        '-p', '--period', default=5, type=int,
        help="sets the period in minutes between each fetch in the cron job (default: %(default)dmin)")
    install_parser.set_defaults(func=install_cron)
    uninstall_parser.set_defaults(func=uninstall_cron)
