# -*: utf-8 -*-
"""
Play py3status's first game module. It's the only game in town.

Treblecross is a degenerate tic-tac toe variant. The game is an octal
game, played on a one-dimensional board and both players play using the
same piece (an X or a black chip). Each player on their turn plays a piece
in an unoccupied space. The player who creates a line of three pieces in a
row loses.

Configuration parameters:
    board_size: specify number of spaces on board to use (default 5)
    button_action: mouse button to play a piece (default 1)
    button_reset: mouse button to reset this module (default 3)
    format: display format for this module (default '{format_board}{result}')
    format_space_empty: display format for empty cells (default '\\|___\\|')
    format_space_occupied: display format for occupied cells (default '\\|_X_\\|')
    format_space_separator: display format for cell separators (default '')

Format placeholders:
    {format_board} game board made of spaces
    {result} game result, eg WIN, LOSE

@author lasers

SAMPLE OUTPUT
{'full_text': '|_X_||_X_||_X_|___||_X_| WIN '}

lose
{'full_text': '|___||_X_||_X_|_X_||_X_| LOSE '}
"""

import random
import time


class Py3status:
    """ """

    # available configuration parameters
    board_size = 5
    button_action = 1
    button_reset = 3
    format = '{format_board}{result}'
    format_space_empty = r'\|___\|'
    format_space_occupied = r'\|_X_\|'
    format_space_separator = ''

    def post_config_hook(self):
        self.board_size = max(self.board_size, 3)
        self.space_format = {}
        for name in ['separator', 'occupied', 'empty']:
            value = getattr(self, f'format_space_{name}', '')
            self.space_format[name] = self.py3.safe_format(value)
        self._reset()

    def _reset(self):
        self.cells = [False] * self.board_size
        self.index = None
        self.next_play = None
        self.result = None

    def _empty_indexes(self):
        return [index for index, occupied in enumerate(self.cells) if not occupied]

    def _has_treblecross(self):
        for index in range(self.board_size - 2):
            if self.cells[index] and self.cells[index + 1] and self.cells[index + 2]:
                return True
        return False

    def _find_winning_index(self):
        for index in range(self.board_size - 2):
            if self.cells[index] and self.cells[index + 1] and not self.cells[index + 2]:
                return index + 2
        return None

    def _set_result(self, result):
        self.result = result
        self.next_play = None
        self.index = None

    def _update_result(self, result):
        if self._has_treblecross():
            self._set_result(result)
            return True
        return False

    def _play_computer_turn(self):
        index = self._find_winning_index()
        if index is None:
            empty_indexes = self._empty_indexes()
            if not empty_indexes:
                return
            index = random.choice(empty_indexes)
        self.cells[index] = True

    def _get_board(self):
        data = []
        for index, occupied in enumerate(self.cells):
            if index and self.space_format['separator']:
                data.extend(self.py3.composite_create(self.space_format['separator']))

            cell = self.py3.composite_create(
                self.space_format['occupied'] if occupied else self.space_format['empty']
            )
            for part in cell:
                part = part.copy()
                part['index'] = index
                data.append(part)

        return data

    def treblecross(self):
        index = self.index
        if index is not None and 0 <= index < self.board_size and not self.cells[index]:
            self.cells[index] = True
            if not self._update_result('lose'):
                self.next_play = time.monotonic() + 1

        if (
            self.result is None
            and self.next_play is not None
            and time.monotonic() >= self.next_play
        ):
            self._play_computer_turn()
            if not self._update_result('win'):
                self.next_play = None

        self.index = None
        cache_until = self.py3.CACHE_FOREVER
        if self.next_play is not None:
            cache_until = self.py3.time_in(1)

        game_data = {
            'result': f" {self.result.upper()} " if self.result else '',
            'format_board': self.py3.composite_create(self._get_board()),
        }

        return {
            'cached_until': cache_until,
            'full_text': self.py3.safe_format(self.format, game_data),
        }

    def on_click(self, event):
        button = event['button']
        if button == self.button_action:
            if self.result is None and self.next_play is None:
                self.index = event['index']
            else:
                self.py3.prevent_refresh()
        elif button == self.button_reset:
            self._reset()
        else:
            self.py3.prevent_refresh()


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
