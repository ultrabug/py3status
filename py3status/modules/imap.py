# -*- coding: utf-8 -*-
"""
Display number of unread messages from IMAP account.

Configuration parameters:
    allow_urgent: display urgency on unread messages (default False)
    cache_timeout: refresh interval for this module (default 60)
    criterion: status of emails to check for (default 'UNSEEN')
    format: display format for this module (default 'Mail: {unseen}')
    hide_if_zero: hide this module when no new mail (default False)
    mailbox: name of the mailbox to check (default 'INBOX')
    password: login password (default None)
    port: number to use (default '993')
    security: login authentication method: 'ssl' or 'starttls'
        (startssl needs python 3.2 or later) (default 'ssl')
    server: server to connect (default None)
    use_idle: use IMAP4 IDLE instead of polling; requires imaplib2,
        compatible server; disables cache_timeout (default False)
    user: login user (default None)

Format placeholders:
    {unseen} number of unread emails

Color options:
    color_new_mail: use color when new mail arrives, default to color_good

@author obb, girst

SAMPLE OUTPUT
{'full_text': 'Mail: 36', 'color': '#00FF00'}
"""
try:
    from imaplib2 import imaplib2 as imaplib
    from threading import Thread  # only necessary with use_idle, which needs imaplib2
    use_lib2 = True  # allow use_idle
except ImportError:
    import imaplib
    use_lib2 = False
from ssl import create_default_context
from socket import error as socket_error
STRING_UNAVAILABLE = 'N/A'


class Py3status:
    """
    """
    # available configuration parameters
    allow_urgent = False
    cache_timeout = 60
    criterion = 'UNSEEN'
    format = 'Mail: {unseen}'
    hide_if_zero = False
    mailbox = 'INBOX'
    password = None
    port = '993'
    security = 'ssl'
    server = None
    use_idle = False
    user = None

    class Meta:
        deprecated = {
            'rename': [
                {
                    'param': 'new_mail_color',
                    'new': 'color_new_mail',
                    'msg': 'obsolete parameter use `color_new_mail`',
                },
                {
                    'param': 'imap_server',
                    'new': 'server',
                    'msg': 'obsolete parameter use `server`',
                },
            ],
        }

    def post_config_hook(self):
        # class variables:
        self.mail_count = None
        self.connection = None
        self.mail_error = None  # cannot throw self.py3.error from thread

        if self.security not in ["ssl", "starttls"]:
            raise ValueError("Unknown security protocol")
        if not use_lib2 and self.use_idle:
            raise ValueError("need imaplib2 for use_idle")
        if self.use_idle:
            self.idle_thread = Thread(target=self._get_mail_count)
            self.idle_thread.start()
        self.port = int(self.port)  # imaplib doesn't care, but imaplib2 does

    def check_mail(self):
        if self.use_idle:
            if not self.idle_thread.isAlive():
                self.idle_thread = Thread(target=self._get_mail_count)
                self.idle_thread.start()
            response = {'cached_until': self.py3.time_in(seconds=1)}
        else:
            self._get_mail_count()
            response = {'cached_until': self.py3.time_in(self.cache_timeout)}
        if self.mail_error is not None:
            self.py3.error(self.mail_error)

        if self.mail_count is None:
            response['color'] = self.py3.COLOR_BAD,
            response['full_text'] = self.py3.safe_format(
                self.format, {'unseen': STRING_UNAVAILABLE})
        elif self.mail_count > 0:
            response['color'] = self.py3.COLOR_NEW_MAIL or self.py3.COLOR_GOOD
            if self.allow_urgent:
                response['urgent'] = True

        if self.mail_count == 0 and self.hide_if_zero:
            response['full_text'] = ''
        else:
            response['full_text'] = self.py3.safe_format(self.format, {'unseen': self.mail_count})

        return response

    def _connection_ssl(self):
        connection = imaplib.IMAP4_SSL(self.server, self.port)
        return connection

    def _connection_starttls(self):
        connection = imaplib.IMAP4(self.server, self.port)
        connection.starttls(create_default_context())
        return connection

    def _disconnect(self):
        try:
            if self.connection is not None:
                self.connection.close()
                self.connection.logout()
        finally:
            self.connection = None

    def _get_mail_count(self):
        try:
            while True:
                if self.connection is None:
                    if self.security == "ssl":
                        self.connection = self._connection_ssl()
                    elif self.security == "starttls":
                        self.connection = self._connection_starttls()

                    self.connection.login(self.user, self.password)

                self.mail_count = 0
                directories = self.mailbox.split(',')

                for directory in directories:
                    self.connection.select(directory)
                    unseen_response = self.connection.search(None, self.criterion)
                    mails = unseen_response[1][0].split()
                    self.mail_count += len(mails)

                if self.use_idle:
                    self.connection.idle()
                else:
                    return
        except socket_error as e:
            self.mail_error = "Socket error - " + e
            self.connection = None
            self.mail_count = None
        except imaplib.IMAP4.error as e:
            self.mail_error = "IMAP error - " + e
            self._disconnect()
            self.mail_count = None
        except Exception as e:
            self.mail_error = "Unknown error - " + e
            self._disconnect()
            self.mail_count = None


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
