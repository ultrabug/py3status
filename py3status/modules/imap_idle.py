# -*- coding: utf-8 -*-
"""
Display number of unread messages from IMAP account. (using IMAP4 IDLE)

Configuration parameters:
    allow_urgent: display urgency on unread messages (default False)
    criterion: status of emails to check for (default 'UNSEEN')
    format: display format for this module (default 'Mail: {unseen}')
    hide_if_zero: hide this module when no new mail (default False)
    mailbox: name of the mailbox to check (default 'INBOX')
    password: login password (default None)
    port: number to use (default '993')
    security: login authentication method: 'ssl' or 'starttls'
        (startssl needs python 3.2 or later) (default 'ssl')
    server: server to connect (default None)
    user: login user (default None)

Format placeholders:
    {unseen} number of unread emails

Color options:
    color_new_mail: use color when new mail arrives, default to color_good

@author obb and girst

SAMPLE OUTPUT
{'full_text': 'Mail: 36', 'color': '#00FF00'}
"""
from imaplib2 import imaplib2
from threading import Thread
from ssl import create_default_context
STRING_UNAVAILABLE = 'N/A'


class Py3status:
    """
    """
    # available configuration parameters
    allow_urgent = False
    criterion = 'UNSEEN'
    format = 'Mail: {unseen}'
    hide_if_zero = False
    mailbox = 'INBOX'
    password = None
    port = '993'
    security = 'ssl'
    server = None
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
        self.mail_count = 0 # will be used to store
        if self.security not in ["ssl", "starttls"]:
            raise ValueError("Unknown security protocol")
        self.idle_thread = self.Idle_Thread(
            mailbox=self.mailbox,
            criterion=self.criterion,
            user=self.user,
            password=self.password,
            server=self.server,
            port=self.port,
            security=self.security)
        self.idle_thread.start()

    class Idle_Thread(Thread):
        def __init__(self, mailbox, criterion, user, password, server, port, security):
            Thread.__init__(self)
            self.connection = None
            self.mailbox = mailbox
            self.criterion = criterion
            self.user = user
            self.password = password
            self.server = server
            self.port = int(port)
            self.security = security
            self.mail_count = 0
        def get_mail_count(self):
            return self.mail_count
        def run(self):
            while True:
                try:
                    if self.connection is None:
                        if self.security == "ssl":
                            self.connection = imaplib2.IMAP4_SSL(self.server, self.port)
                        elif self.security == "starttls":
                            self.connection = imaplib2.IMAP4(self.server, self.port)
                            self.connection.starttls(create_default_context())
                        self.connection.login(self.user, self.password)

                    self.mail_count = 0
                    directories = self.mailbox.split(',')

                    for directory in directories:
                        self.connection.select(directory)
                        unseen_response = self.connection.search(None, self.criterion)
                        mails = unseen_response[1][0].split()
                        self.mail_count += len(mails)

                    self.connection.idle()
                except Exception as e:
                    import time
                    time.sleep(1)
                    if self.connection is not None:
                        self.connection.close()
                        self.connection.logout()
                    self.connection = None

    def check_mail(self):
        mail_count = self.idle_thread.get_mail_count()

        response = {'cached_until': self.py3.time_in(seconds=1)}

        if mail_count is None:
            response['color'] = self.py3.COLOR_BAD,
            response['full_text'] = self.py3.safe_format(
                self.format, {'unseen': STRING_UNAVAILABLE})
        elif mail_count > 0:
            response['color'] = self.py3.COLOR_NEW_MAIL or self.py3.COLOR_GOOD
            if self.allow_urgent:
                response['urgent'] = True

        if mail_count == 0 and self.hide_if_zero:
            response['full_text'] = ''
        else:
            response['full_text'] = self.py3.safe_format(self.format, {'unseen': mail_count})

        return response




if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
