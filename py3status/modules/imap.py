# -*- coding: utf-8 -*-
# FIXME new_mail_color param
"""
Display the unread messages count from your IMAP account.

Configuration parameters:
    cache_timeout: how often to run this check
    criterion: status of emails to check for
    format: format to display
    hide_if_zero: don't show on bar if 0
    imap_server: IMAP server to connect to
    mailbox: name of the mailbox to check
    new_mail_color: what color to output on new mail
    password: login password
    port: IMAP server port
    user: login user
    base64: use base64 encoded password (bool) (default: False)

Format of status string placeholders:
    {unseen} number of unread emails

@author obb
"""

import imaplib
from time import time
import base64


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 60
    criterion = 'UNSEEN'
    hide_if_zero = False
    imap_server = '<IMAP_SERVER>'
    mailbox = 'INBOX'
    format = 'Mail: {unseen}'
    new_mail_color = ''
    password = '<PASSWORD>'
    port = '993'
    user = '<USERNAME>'
    base64 = False

    def check_mail(self):
        mail_count = self._get_mail_count()

        response = {'cached_until': time() + self.cache_timeout}

        if not self.new_mail_color:
            self.new_mail_color = self.py3.COLOR_GOOD

        if mail_count == 'N/A':
            response['full_text'] = mail_count
        elif mail_count != 0:
            response['color'] = self.new_mail_color
            response['full_text'] = self.format.format(unseen=mail_count)
        else:
            if self.hide_if_zero:
                response['full_text'] = ''
            else:
                response['full_text'] = self.format.format(unseen=mail_count)

        return response

    def _get_mail_count(self):
        try:
            mail_count = 0
            directories = self.mailbox.split(',')
            connection = imaplib.IMAP4_SSL(self.imap_server, self.port)
            connection.login(self.user, self.passwd)

            for directory in directories:
                connection.select(directory)
                unseen_response = connection.search(None, self.criterion)
                mails = unseen_response[1][0].split()
                mail_count += len(mails)

            connection.close()
            return mail_count

        except:
            return 'N/A'

    @property
    def passwd(self):
        if self.base64:
            return base64.b64decode(self.password).decode('utf-8')
        return self.password


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
