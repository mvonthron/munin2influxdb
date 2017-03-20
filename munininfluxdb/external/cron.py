"""
Default CRON implementation.

This module represents a "border" to the outside world and provides a "seam" for
dependency injection/patching/mocking. Or easier replacement for the underlying
CRON library.
"""
import crontab


def remove_by_comment(user, comment):
    """
    Searches for CRON entries of *user* containing *comment* as commment. Each
    entry with that comment is removed from the CRONtab.

    :return: The number of deleted jobs.
    :rtype: int
    """
    cron = crontab.CronTab(user=user)
    jobs = list(cron.find_comment(comment))
    cron.remove(*jobs)
    cron.write()
    return len(jobs)


def add_with_comment(user, cmd, period, comment):
    """
    Adds a new entry running *cmd* for *uer* to the CRONtab. The entry will be
    scheduled to run each *period* minutes. For identification (and removal by
    the ``uninstall`` command, the entry is marked with the comment in
    *comment*.

    :return: Whether the operation was successful or not.
    :rtype: bool
    """
    cron = crontab.CronTab(user=user)
    job = cron.new(command=cmd, user=user, comment=comment)
    job.minute.every(period)
    success = job.is_valid() and job.is_enabled()
    if success:
        cron.write()
    return success
