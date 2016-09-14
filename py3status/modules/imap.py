# -*- coding: utf-8 -*-
# FIXME new_mail_color param
"""
Display the unread messages count from your IMAP account.

Configuration parameters:
    cache_timeout: how often to run this check (default 60)
    criterion: status of emails to check for (default 'UNSEEN')
    format: format to display (default 'Mail: {unseen}')
    hide_if_zero: don't show on bar if False (default False)
    imap_server: IMAP server to connect to (default '<IMAP_SERVER>')
    mailbox: name of the mailbox to check (default 'INBOX')
    new_mail_color: what color to output on new mail (default '')
    password: login password (default '<PASSWORD>')
    port: IMAP server port (default '993')
    user: login user (default '<USERNAME>')

Format placeholders:
    {unseen} number of unread emails

@author obb
"""

import imaplib


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

    def _get_mail_count(self):
        try:
            mail_count = 0
            directories = self.mailbox.split(',')
            connection = imaplib.IMAP4_SSL(self.imap_server, self.port)
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
