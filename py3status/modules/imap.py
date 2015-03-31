# -*- coding: utf-8 -*-
"""
Display the unread messages count from your IMAP account.

Configuration parameters:
    - cache_timeout : how often to run this check
    - criterion : status of emails to check for
    - hide_if_zero : don't show on bar if 0
    - imap_server : IMAP server to connect to
    - mailbox : name of the mailbox to check
    - name : format to display
    - new_mail_color : what color to output on new mail
    - password : login password
    - port : IMAP server port
    - user : login user

@author obb
"""

import imaplib
from time import time


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 60
    criterion = 'UNSEEN'
    hide_if_zero = False
    imap_server = '<IMAP_SERVER>'
    mailbox = 'INBOX'
    name = 'Mail: {unseen}'
    new_mail_color = ''
    password = '<PASSWORD>'
    port = '993'
    user = '<USERNAME>'

    def check_mail(self, i3s_output_list, i3s_config):
        mail_count = self._get_mail_count()

        response = {
            'cached_until': time() + self.cache_timeout
        }

        if not self.new_mail_color:
            self.new_mail_color = i3s_config['color_good']

        if mail_count == 'N/A':
            response['color'] = ''
            response['full_text'] = mail_count
        elif mail_count != 0:
            response['color'] = self.new_mail_color
            response['full_text'] = self.name.format(unseen=mail_count)
        else:
            response['color'] = ''
            if self.hide_if_zero:
                response['full_text'] = ''
            else:
                response['full_text'] = self.name.format(unseen=mail_count)

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
    Test this module by calling it directly.
    """
    from time import sleep
    x = Py3status()
    config = {
        'color_good': '#00FF00',
        'color_bad': '#FF0000',
    }
    while True:
        print(x.check_mail([], config))
        sleep(1)
