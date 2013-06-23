class Py3status:
    """
    Empty and basic py3status class.

    NOTE: py3status will NOT execute :
        - methods starting with '_'
        - methods decorated by @property and @staticmethod
    """
    def empty(self, json, i3status_config):
        """
        This method will return an empty text message, so it will NOT be displayed.
        If you want something displayed you should write something in the 'full_text' key of your response.
        See the i3bar protocol spec for more information:
            http://i3wm.org/docs/i3bar-protocol.html
        """
        response = {'full_text' : '', 'name' : 'empty'}
        return (0, response)
