r"""
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

IMAP Subscriptions:
    You can specify a list of filters to decide which folders to search.
    By default, we search only the INBOX folder (ie: `['^INBOX$']`). We
    can use regular expressions, so if you use more than one, it would
    be joined by a logical operator `or`.

    `'.*'` will match all folders.
    `'pattern'` will match folders containing `pattern`.
    `'^pattern'` will match folders beginning with `pattern`.
    `'pattern$'` will match folders ending with `pattern`.
    `'^((?![Ss][Pp][Aa][Mm]).)*$'` will match all folders
    except for every possible case of `spam` folders.

    For more documentation, see https://docs.python.org/3/library/re.html
    and/or any regex builder on the web. Don't forget to escape characters.

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
                                             #  <---│----│ no filters to
                'port': 993,                 #      │    │ search folders, use
                                             #      │    │ filters ['^INBOX$']
            },                               #      │    │
            {                                #      │    └── {imap_2}
                'name': 'work',              # <----│---------└── {work}
                'user': 'tobes',             #      │
                'password': 'i_love_python', #
                'server': 'imap.yahoo.com',  #
                                             # <---- no port, use port 993
                'urgent': False,             # <---- disable urgent
                                             #       for this account
                'filters': ['^INBOX$']       # <---- specify a list of filters
                                             #       to search folders
                'log': True,                 # <---- print a list of folders
            }                                #       to filter in the log
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
import os
from csv import reader
from imaplib import IMAP4_SSL, IMAP4
from pathlib import Path

STRING_MISSING = "missing {} {}"
STRING_INVALID_NAME = "invalid name `{}`"
STRING_INVALID_BOX = "invalid mailbox `{}`"
STRING_INVALID_FILTER = "invalid imap filters `{}`"


class Py3status:
    """"""

    # available configuration parameters
    accounts = {}
    cache_timeout = 60
    format = r"\?not_zero Mail {mail}|No Mail"
    thresholds = []

    def post_config_hook(self):
        if not self.accounts:
            raise Exception("missing accounts")

        self.first_run = True
        self.mailboxes = {}
        mailboxes = ["Maildir", "mbox", "mh", "Babyl", "MMDF", "IMAP"]
        lowercased_names = [x.lower() for x in mailboxes]
        reserved_names = lowercased_names + ["mail"]
        for mail, accounts in self.accounts.items():
            if mail not in lowercased_names:
                raise Exception(STRING_INVALID_BOX.format(mail))
            self.mailboxes[mail] = []
            for account in accounts:
                if "name" in account:
                    name = account["name"]
                    strip = name.rstrip("_0123456789")
                    if any(x in [name, strip] for x in reserved_names):
                        raise Exception(STRING_INVALID_NAME.format(name))
                    reserved_names.append(name)
                account.setdefault("urgent", True)
                if mail == "imap":
                    for v in ["user", "password", "server"]:
                        if v not in account:
                            raise Exception(STRING_MISSING.format(mail, v))
                    account.setdefault("port", 993)
                    if "filters" in account:
                        filters = account["filters"]
                        if not isinstance(filters, list):
                            raise Exception(STRING_INVALID_FILTER.format(filters))
                    else:
                        account["filters"] = ["^INBOX$"]
                    account["folders"] = []
                    self.mailboxes[mail].append(account)
                else:
                    for box in mailboxes[:-1]:
                        if mail == box.lower():
                            if "path" not in account:
                                raise Exception(STRING_MISSING.format(mail, "path"))
                            path = os.path.expandvars(
                                Path(account["path"]).expanduser()
                            )
                            if not path.exists():
                                path = f"path: {path}"
                                raise Exception(STRING_MISSING.format(mail, path))
                            account["box"] = box
                            account["path"] = path
                            self.mailboxes[mail].append(account)
                            break

        self.thresholds_init = self.py3.get_color_names_list(self.format)

    def mail(self):
        mail_data = {"mail": 0, "urgent": False}
        for k, v in self.mailboxes.items():
            mail_data[k] = 0
            for i, account in enumerate(v, 1):
                if k == "imap":
                    inbox = IMAP4_SSL(account["server"], account["port"])
                    inbox.login(account["user"], account["password"])

                    if self.first_run:
                        import re

                        filters = "|".join(account.pop("filters"))
                        objs = [x.decode() for x in inbox.list()[1]]
                        folders = [x[-1] for x in reader(objs, delimiter=" ")]
                        lines = [f"===== IMAP {i} ====="]
                        for name in folders:
                            subscribed = " "
                            try:
                                if re.search(filters, name):
                                    subscribed = "x"
                                    folder = name.replace("\\", "\\\\")
                                    folder = folder.replace('"', '\\"')
                                    folder = f'"{folder}"'
                                    account["folders"].append(folder)
                            except re.error:
                                account["folders"] = []
                                break
                            lines.append(f"[{subscribed}] {name}")
                        if not account["folders"]:
                            self.py3.error(
                                STRING_INVALID_FILTER.format(filters),
                                self.py3.CACHE_FOREVER,
                            )
                        if account.get("log") is True:
                            for line in lines:
                                self.py3.log(line)

                    count_mail = 0
                    for folder in account["folders"]:
                        if inbox.select(folder, readonly=True)[0] == "OK":
                            imap_data = inbox.search(None, "(UNSEEN)")
                            count_mail += len(imap_data[1][0].split())
                        else:
                            account["folders"].remove(folder)
                    try:
                        inbox.close()
                        inbox.logout()
                    except IMAP4.error:
                        pass
                else:
                    inbox = getattr(mailbox, account["box"])(
                        account["path"], create=False
                    )
                    count_mail = len(inbox)
                    inbox.close()
                if "name" in account:
                    mail_data[account["name"]] = count_mail
                if account["urgent"] and count_mail:
                    mail_data["urgent"] = True
                mail_data[f"{k}_{i}"] = count_mail
                mail_data["mail"] += count_mail
                mail_data[k] += count_mail

        for x in self.thresholds_init:
            if x in mail_data:
                self.py3.threshold_get_color(mail_data[x], x)

        self.first_run = False

        response = {
            "cached_until": self.py3.time_in(self.cache_timeout),
            "full_text": self.py3.safe_format(self.format, mail_data),
        }
        if mail_data["urgent"]:
            response["urgent"] = True
        return response


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
