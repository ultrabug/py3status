# -*- coding: utf-8 -*-
"""
Display number of messages in various mailbox formats.
This module supports Maildir, mbox, MH, Babyl, MMDF, and IMAP.

Configuration parameters:
    accounts: specify a dict consisting of mailbox types and a list of dicts
        consisting of mailbox settings and/or paths to use (default {})
    cache_timeout: refresh interval for this module (default 60)
    format: display format for this module
        (default '\?not_zero Mail {mail}|No Mail')
    thresholds: specify color thresholds to use (default [])

Format placeholders:
    {mail}    number of messages
    {maildir} number of Maildir messages
    {mbox}    number of mbox messages
    {mh}      number of MH messages
    {babyl}   number of Babyl messages
    {mmdf}    number of MMDF messages
    {imap}    number of IMAP messages

    We can divide mailbox, eg `{maildir}`, into numbered placeholders based
    on number of mailbox accounts, eg `{maildir_1}`, and if we add `name` to
    a mailbox account, we can use `{name}` placeholder instead, eg `{home}`.

Color thresholds:
    xxx: print a color based on the value of `xxx` placeholder

Examples:
```
# add multiple accounts
mail {                                       #
    accounts = {                             #     {mail}
        'maildir': [                         #      ├── {maildir}
            {'path': '~/.mutt'},             #      │    ├── {maildir_1}
            {'path': '~/Mail'},              #      │    └── {maildir_2}
        ],                                   #      │
        'mbox': [                            #      ├── {mbox}
            {'path': '~/home.mbox'},         #      │    ├── {mbox_1}
            {                                #      │    ├── {mbox_2}
                'name': 'local',             # <----│----│----└── {local}
                'path': '~/mbox'             #      │    │
            },                               #      │    │
            {                                #      │    └── {mbox_3}
                'name': 'debian',            # <----│---------└── {debian}
                'path': '/var/mail/$USER'    #      │
                'urgent': False,             # <----│---- disable urgent
            },                               #      │
        ],                                   #      │
        'mh': [                              #      ├── {mh}
            {'path': '~/mh_mail'},           #      │    └── {mh_1}
        ],                                   #      │
        'babyl': [                           #      ├── {babyl}
            {'path': '~/babyl_mail'},        #      │    └── {babyl_1}
        ],                                   #      │
        'mmdf': [                            #      ├── {mmdf}
            {'path': '~/mmdf_mail'},         #      │    └── {mmdf_1}
        ]                                    #      │
        'imap': [                            #      ├── {imap}
            {                                #      │    ├── {imap_1}
                'name': 'home',              # <----│----│----└── {home}
                'user': 'lasers',            #      │    │
                'password': 'kiss_my_butt!', #      │    │
                'server': 'imap.gmail.com',  #      │    │ 
                'port': 993,                 #      │    │
            },                               #      │    │
            {                                #      │    └── {imap_2}
                'name': 'work',              # <----│---------└── {work}
                'user': 'tobes',             #      │
                'password': 'i_love_python', #
                'server': 'imap.yahoo.com',  #
                                             # <---- no port, use port 993
                'urgent': False,             # <---- disable urgent
            }                                #
        ]
    }
    allow_urgent = False             <---- disable urgent for all accounts
}

# add colors, disable urgent
mail {
    format = '[\?color=mail&show Mail] {mail}'
    thresholds = [(1, 'good'), (5, 'degraded'), (15, 'bad')]
    allow_urgent = False
}

# identify the mailboxes, remove what you don't need
mail {
    format = '[\?color=mail '
    format += '[\?if=imap&color=#00ff00 IMAP ]'
    format += '[\?if=maildir&color=#ffff00 MAILDIR ]'
    format += '[\?if=mbox&color=#ff0000 MBOX ]'
    format += '[\?if=babyl&color=#ffa500 BABYL ]'
    format += '[\?if=mmdf&color=#00bfff MMDF ]'
    format += '[\?if=mh&color=#ee82ee MH ]'
    format += ']'
    format += '[\?not_zero&color Mail {mail}|No Mail]'
}

# individual colorized mailboxes, remove what you don't need
mail {
    format = '[\?if=imap&color=#00ff00 IMAP] {imap} '
    format += '[\?if=maildir&color=#ffff00 MAILDIR] {maildir} '
    format += '[\?if=mbox&color=#ff0000 MBOX] {mbox} '
    format += '[\?if=babyl&color=#ffa500 BABYL] {babyl} '
    format += '[\?if=mmdf&color=#00bfff MMDF] {mmdf} '
    format += '[\?if=mh&color=#ee82ee MH] {mh}'
    allow_urgent = False
}
```

@author lasers

SAMPLE OUTPUT
{'full_text': 'Mail 15', 'urgent': True}

identified
[
    {'full_text': 'IMAP ', 'color': '#00ff00'},
    {'full_text': 'MAILDIR ', 'color': '#ffff00'},
    {'full_text': 'MBOX ', 'color': '#ff0000'},
    {'full_text': 'Mail 15'},
]

individualized
[
    {'full_text': 'IMAP ', 'color': '#00ff00'}, {'full_text': 'Mail 10 '},
    {'full_text': 'MAILDIR ', 'color': '#ffff00'}, {'full_text': 'Mail 2 '},
    {'full_text': 'MBOX ', 'color': '#ff0000'}, {'full_text': 'Mail 3'},
]

no_mail
{'full_text': 'No Mail'}
"""

import mailbox
from imaplib import IMAP4_SSL
from os.path import exists, expanduser, expandvars
STRING_MISSING = 'missing {} {}'


class Py3status:
    """
    """
    # available configuration parameters
    accounts = {}
    cache_timeout = 60
    format = '\?not_zero Mail {mail}|No Mail'
    thresholds = []

    def post_config_hook(self):
        if not self.accounts:
            raise Exception('missing accounts')

        self.mailboxes = {}
        mailboxes = ['Maildir', 'mbox', 'mh', 'Babyl', 'MMDF', 'IMAP']
        for mail, accounts in self.accounts.items():
            if mail not in [x.lower() for x in mailboxes]:
                continue
            self.mailboxes[mail] = []
            for account in accounts:
                account.setdefault('urgent', True)
                if mail == 'imap':
                    for v in ['user', 'password', 'server']:
                        if v not in account:
                            raise Exception(STRING_MISSING.format(mail, v))
                    account.setdefault('port', 993)
                    self.mailboxes[mail].append(account)
                else:
                    for box in mailboxes[:-1]:
                        if mail == box.lower():
                            if 'path' not in account:
                                raise Exception(
                                    STRING_MISSING.format(mail, 'path')
                                )
                            path = expandvars(expanduser(account['path']))
                            if not exists(path):
                                path = 'path: {}'.format(path)
                                raise Exception(
                                    STRING_MISSING.format(mail, path)
                                )
                            account['box'] = box
                            account['path'] = path
                            self.mailboxes[mail].append(account)
                            break

        self.thresholds_init = self.py3.get_color_names_list(self.format)

    def mail(self):
        mail_data = {'mail': 0, 'urgent': False}
        for k, v in self.mailboxes.items():
            mail_data[k] = 0
            for i, account in enumerate(v, 1):
                if k == 'imap':
                    inbox = IMAP4_SSL(account['server'], account['port'])
                    inbox.login(account['user'], account['password'])
                    inbox.select(readonly=True)
                    imap_data = inbox.search(None, '(UNSEEN)')
                    count_mail = len(imap_data[1][0].split())
                    inbox.close()
                    inbox.logout()
                else:
                    inbox = getattr(mailbox, account['box'])(
                        account['path'], create=False)
                    count_mail = len(inbox)
                    inbox.close()
                if 'name' in account:
                    mail_data[account['name']] = count_mail
                if account['urgent'] and count_mail:
                    mail_data['urgent'] = True
                mail_data['%s_%s' % (k, i)] = count_mail
                mail_data['mail'] += count_mail
                mail_data[k] += count_mail

        for x in self.thresholds_init:
            if x in mail_data:
                self.py3.threshold_get_color(mail_data[x], x)

        response = {
            'cached_until': self.py3.time_in(self.cache_timeout),
            'full_text': self.py3.safe_format(self.format, mail_data)
        }
        if mail_data['urgent']:
            response['urgent'] = True
        return response


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
