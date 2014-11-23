# -*- coding: utf8 -*-

from time import time
import imaplib

"""
Module displaying the number of unread messages
on an IMAP inbox (configurable).

@author obb
"""


class Py3status:

    def __init__(self):
        self.service_name = 'Mail'
        self.imap_server = '<IMAP_SERVER>'
        self.port = '993'

        self.user = '<USERNAME>'
        self.password = '<PASSWORD>'

        self.mailbox = 'INBOX'
        self.criterion = 'UNSEEN'

        self.check_frequency = 60

    def check_mail(self, json, i3status_config):
        mail_count = self._get_mail_count()

        response = {
            'name': self.service_name + '_checker',
            'full_text': '{}: {}'.format(self.service_name, mail_count),
            'cached_until': time() + self.check_frequency
        }

        new_mail_color = i3status_config['color_good']
        check_failed_color = i3status_config['color_bad']

        if mail_count == 'N/A':
            response['color'] = check_failed_color
        elif mail_count != '0':
            response['color'] = new_mail_color

        return (0, response)

    def _get_mail_count(self):
        try:
            connection = imaplib.IMAP4_SSL(self.imap_server, self.port)
            connection.login(self.user, self.password)
            connection.select(self.mailbox)
            unseen_response = connection.search(None, self.criterion)
            mails = unseen_response[1][0].split()
            mail_count = len(mails)
            return mail_count
        except:
            return 'N/A'
