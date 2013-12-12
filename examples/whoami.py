from getpass import getuser
from time import time


class Py3status:
    """
    Simply output the currently logged in user in i3bar.

    Inspired by i3 FAQ:
        https://faq.i3wm.org/question/1618/add-user-name-to-status-bar/
    """
    def whoami(self, i3status_output_json, i3status_config):
        """
        We use the getpass module to get the current user.
        """
        # the current user doesnt change so much, cache it good
        CACHE_TIMEOUT = 600

        # here you can change the format of the output
        # default is just to show the username
        username = '{}'.format(getuser())

        # set, cache and return the output
        response = {'full_text': username, 'name': 'whoami'}
        response['cached_until'] = time() + CACHE_TIMEOUT
        return (0, response)
