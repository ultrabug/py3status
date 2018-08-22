#!/usr/bin/env python

"""Show the number of unread mails in maildir format inboxes.

Configuration parameters:
    cache_timeout: refresh interval for this module (default 10)
    error_timeout: error message reset interval (default 10)
    format: display format for this module (default '{name} {unread}')
    mailboxes: space-separated list of maildirs to monitor (default '')
    name: module name (default 'MAIL:')

Format placeholders:
    {name} module name
    {unread} number of unread mails

@author tablet-mode
@license BSD

SAMPLE OUTPUT
{'full_text': 'MAIL: 4', 'color': '#FFFF00'}

"""

from errno import ENOENT
from mailbox import Maildir, NoSuchMailboxError
from os import listdir, path
from shlex import split
from time import time


class MaildirException(Exception):
    """Custom maildir exception."""

    def __init__(self, exception):
        """Initialisation."""
        self.exception = exception

    def __str__(self):
        """Prepend message with 'maildir: '."""
        return "maildir: {exception}".format(exception=self.exception)


class Data:
    """Aquire data."""

    def __init__(self, mailboxes):
        """Initialisation."""
        self.read_mailboxes(mailboxes)
        self.error = (None, None)

    def read_mailboxes(self, mailboxes):
        """Return list of mailboxes.

        Raise exception on invalid mailbox.

        """
        mboxes = []
        state = []
        unread = []
        if mailboxes:
            for mdir in mailboxes:
                try:
                    mbox = Maildir(mdir, create=False)
                    mbox.keys()
                    mboxes.append(mbox)
                    state.append('')
                    unread.append(0)
                except NoSuchMailboxError:
                    raise MaildirException(
                        "invalid path: {path}".format(path=mdir))
                except IOError as err:
                    if err.errno == ENOENT:
                        raise MaildirException(
                            "invalid maildir: {path}".format(path=mdir))
                    raise MaildirException(
                        "failed to read maildir at {path}: {error}".format(
                            path=mdir, error=err))
        self.mboxes = mboxes
        self.mbox_state = state
        self.unread = unread

    def _get_unread_maildir(self, mbox):
        """Shortcut for maildir format.

        Get number of unread mails by simply counting the number of files in
        the 'new' folder.

        """
        mdir = mbox._paths['new']
        unread = len(
            [item for item in listdir(mdir) if path.isfile(path.join(
                mdir, item))])
        return unread

    def get_unread(self):
        """Return number of unread emails."""
        unread_mails = 0
        if not self.mboxes:
            unread_mails = 'no mailbox configured'
            return unread_mails

        last_state = self.mbox_state[:]
        unread_per_box = self.unread[:]
        for i, mbox in enumerate(self.mboxes):
            mbox.keys()
            self.mbox_state[i] = mbox._toc
            if self.mbox_state[i] == last_state[i]:
                pass
            else:
                unread_per_box[i] = 0
                if isinstance(mbox, Maildir):
                    unread_per_box[i] = self._get_unread_maildir(mbox)
                else:
                    for message in mbox:
                        flags = message.get_flags()
                        if 'S' not in flags:
                            unread_per_box[i] += 1
        self.unread = unread_per_box
        unread_mails = sum(unread_per_box)

        return unread_mails


class Py3status:
    """This is where all the py3status magic happens."""

    cache_timeout = 10
    error_timeout = 10
    format = '{name} {unread}'
    mailboxes = ''
    name = 'MAIL:'

    def __init__(self):
        """Initialisation."""
        self.data = None

    def _validate_config(self):
        """Validate configuration."""
        msg = []

        if type(self.name) != str:
            msg.append("invalid name")

        if msg:
            self.data.error = ("configuration error: {}".format(
                ", ".join(msg)), -1)

    def maildir(self):
        """Return response for i3status bar."""
        response = {'full_text': ''}

        # use split from the shlex lib here because it allows you to escape
        # whitespaces
        if not self.data:
            self.data = Data(split(self.mailboxes))

        # Reset error message
        # -1 means we can't recover from this error
        if (self.data.error[0] and
                (self.data.error[1] + self.error_timeout < time() and
                    self.data.error[1] != -1)):
            self.data.error = (None, None)

        unread = self.data.get_unread()

        if isinstance(unread, str):
            response['color'] = self.py3.COLOR_BAD
        else:
            if unread > 0:
                response['color'] = self.py3.COLOR_DEGRADED
        response['full_text'] = self.py3.safe_format(
            self.format, {'name': self.name, 'unread': unread})

        response['cached_until'] = self.py3.time_in(self.cache_timeout)

        return response


if __name__ == "__main__":
    """Run module in test mode."""
    from p3status.module_test import module_test
    module_test(Py3status)
