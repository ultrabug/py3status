# -*- coding: utf-8 -*-
# FIXME new_mail_color param
"""
Display number of unread messages from IMAP account.

Configuration parameters:
    cache_timeout: how often to run this check (default 60)
    criterion: status of emails to check for (default 'UNSEEN')
    format: format to display (default 'Mail: {unseen}')
    hide_if_zero: don't show on bar if True (default False)
    imap_server: IMAP server to connect to (default '<IMAP_SERVER>')
    mailbox: name of the mailbox to check (default 'INBOX')
    new_mail_color: what color to output on new mail (default '')
    password: login password (default '<PASSWORD>')
    port: IMAP server port (default '993')
    security: what authentication method is used: 'ssl' or 'starttls'
        (startssl needs python 3.2 or later) (default 'ssl')
    user: login user (default '<USERNAME>')

Format placeholders:
    {unseen} number of unread emails

@author obb
"""

import imaplib
from ssl import create_default_context


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 60
    criterion = 'UNSEEN'
    format = 'Mail: {unseen}'
    hide_if_zero = False
    imap_server = '<IMAP_SERVER>'
    mailbox = 'INBOX'
    new_mail_color = ''
    password = '<PASSWORD>'
    port = '993'
    security = 'ssl'
    user = '<USERNAME>'

    def post_config_hook(self):
        if self.security not in ["ssl", "starttls"]:
            raise ValueError("Unknown security protocol")

    def check_mail(self):
        mail_count = self._get_mail_count()

        response = {'cached_until': self.py3.time_in(self.cache_timeout)}

        if not self.new_mail_color:
            self.new_mail_color = self.py3.COLOR_GOOD

        if mail_count == 'N/A':
            response['full_text'] = mail_count
        elif mail_count != 0:
            response['color'] = self.new_mail_color
            response['full_text'] = self.py3.safe_format(
                self.format, {'unseen': mail_count}
            )
        else:
            if self.hide_if_zero:
                response['full_text'] = ''
            else:
                response['full_text'] = self.py3.safe_format(
                    self.format, {'unseen': mail_count}
                )

        return response

    def _connection_ssl(self):
        connection = imaplib.IMAP4_SSL(self.imap_server, self.port)
        return connection

    def _connection_starttls(self):
        connection = imaplib.IMAP4(self.imap_server, self.port)
        connection.starttls(create_default_context())
        return connection

    def _get_mail_count(self):
        try:
            mail_count = 0
            directories = self.mailbox.split(',')

            if self.security == "ssl":
                connection = self._connection_ssl()
            elif self.security == "starttls":
                connection = self._connection_starttls()

            connection.login(self.user, self.password)

            for directory in directories:
                connection.select(directory)
                unseen_response = connection.search(None, self.criterion)
                mails = unseen_response[1][0].split()
                mail_count += len(mails)

            connection.close()
            return mail_count

        except:
            return 'N/A'


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
