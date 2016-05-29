# -*- coding: utf-8 -*-

"""
Displays number of unread emails in an email account. Default settings are set up for gmail.
If you want to use this with a gmail account then you only need to provide email_account and email_password in the i3status config.

Configuration parameters:
    cache_timeout: How often in seconds this module is refreshed (default 600)
    email_account: Full username login for email (example: email.example@server.com)
    email_password: Login password. Usage of app-passwords for gmail are strongly recommended so that your email password is not stored in plaintext.
    imap_url: Imap server url (default: 'imap.gmail.com')
    imap_port: Imap server port (default: '993')
    format: Display format to use (default: 'Mail: {new_mail}')

Format status string paramterers:
    {new_mail} Number of unread email

@author Daniel Jenssen <daerandin@gmail.com>
@license GPL3
"""
import imaplib

from time import time

class Py3status:

    # Configuration options
    cache_timeout = 600
    email_account = ''
    email_password = ''
    imap_url = 'imap.gmail.com'
    imap_port = '993'
    format = 'Mail: {new_mail}'

    def __init__(self, account='', password=''):
        if account:
            self.email_account = account
        if password:
            self.email_password = password

    def get_new_mail(self, i3s_output_list, i3s_config):
        number_of_mail = self._connect_and_get()
        results = self.format.format(new_mail=str(number_of_mail))

        response = {
                'cached_until': time() + self.cache_timeout,
                'full_text': results
                }
        return response


    def _connect_and_get(self):
        conn = imaplib.IMAP4_SSL(self.imap_url, self.imap_port)
        conn.login(self.email_account, self.email_password)
        conn.select(mailbox='INBOX', readonly=True)
        typ, messages = conn.search(None, 'UNSEEN')
        conn.close()
        conn.logout()

        return len(messages[0].split())

if __name__ == "__main__":
    """
    Test this module directly.
    Requires two arguments: email_account, email_password
    """

    from time import sleep
    from sys import argv

    x = Py3status(argv[1], argv[2])
    config = {
            'color_bad': '#FF0000',
            'color_degraded': '#FFFF00',
            'color_good': '#00FF00',
            }
    while True:
        print(x.get_new_mail([], config))
        sleep(1)
