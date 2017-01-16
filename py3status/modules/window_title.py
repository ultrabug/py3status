# -*- coding: utf-8 -*-
"""
Display current window title.

Prints the name of focused window at frequent intervals.

Configuration parameters:
    cache_timeout: How often we refresh this module in seconds (default 0.5)
    format: display format for window_title (default '{title}')
    max_width: If width of title is greater, shrink it and add '...'
        (default 120)

@author shadowprince
@license Eclipse Public License

SAMPLE OUTPUT
{'full_text': u'business_plan_final3a.doc'}
"""

from json import loads


def find_focused(tree):
    if type(tree) == list:
        for el in tree:
            res = find_focused(el)
            if res:
                return res
    elif type(tree) == dict:
        if tree['focused']:
            return tree
        else:
            return find_focused(tree['nodes'] + tree['floating_nodes'])
    return ''


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 0.5
    format = '{title}'
    max_width = 120

    def __init__(self):
        self.title = ''

    def window_title(self):
        tree = loads(self.py3.command_output('i3-msg -t get_tree'))
        window = find_focused(tree)

        if not window or window.get('name') is None or window.get('type') == 'workspace':
            title = ''
        elif len(window['name']) > self.max_width:
            title = u"...{}".format(window['name'][-(self.max_width - 3):])
        else:
            title = window['name']

        return {
            'cached_until': self.py3.time_in(self.cache_timeout),
            'full_text': self.py3.safe_format(self.format, {'title': title}),
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
