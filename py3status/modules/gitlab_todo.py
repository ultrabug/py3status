# -*- coding: utf-8 -*-

# python-gitlab
from gitlab import Gitlab


class Py3status:
    gitlab_url = 'https://gitlab.com'
    auth_token = "give me a token"
    trigger_low = 3
    trigger_hi = 6
    color_low = "#4286f4"
    color_hi = "#cb4b16"

    def __init__(self):
        self.full_text = 'Unknown'
        self.color = "#859900"

    def _get_todos(self):
        """ Returns the todos objects, empty list otherwise.
        """
        try:
            todos = []
            gl = Gitlab(self.gitlab_url, self.auth_token)
            gl.auth()
            todos = gl.todos.list(per_page=50)
        except Exception as e:
            raise Exception("Unable to retrieve todos :{:.20} ...".format(e.error_message))
        else:
            return todos

    def gitlab_todo(self):
        try:
            todos = self._get_todos()
            todos_number = len(todos)
            self.full_text = '{} todos'.format(todos_number)
            if todos_number > self.trigger_low:
                self.color = self.color_low
            if todos_number > self.trigger_hi:
                self.color = self.color_hi
        except Exception as e:
            self.full_text = '{}'.format(e)
        finally:
            return {
                    'full_text': self.full_text,
                    'color': self.color,
            }


if __name__ == '__main__':
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
