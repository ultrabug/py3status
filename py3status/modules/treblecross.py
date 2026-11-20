"""
Play py3status's first game module. It's the only game in town.

Treblecross is a degenerate tic-tac toe variant. The game is an octal game,
played on a one-dimensional board and both players play using the same piece
(an X or a black chip). Each player on their turn plays a piece in an
unoccupied space. In standard play, the player who creates a line of three
pieces wins. In inverse (misere) play, that player loses.

Configuration parameters:
    board_size: specify number of spaces, otherwise random (default None)
    button_action: mouse button to play a piece (default 1)
    button_reset: mouse button to reset the game (default 3)
    format: display format for this module (default '{variant}{format_board}{result}')
    format_space_empty: display format for empty cells (default '\\|___\\|')
    format_space_occupied: display format for occupied cells (default '\\|_X_\\|')
    format_space_separator: display format for cell separators (default '')
    variant: specify standard, inverse, or None for random (default None)

Format placeholders:
    {format_board} game board made of spaces
    {result} game result, eg WIN, LOSE
    {variant} game variant, eg Standard, Inverse

@author lasers

SAMPLE OUTPUT
{'full_text': 'Standard|_X_||_X_||_X_||___||_X_|WIN'}

inverse
{'full_text': 'Inverse|___||_X_||_X_||_X_||_X_|LOSE'}
"""

import random
import time


class Py3status:
    """ """

    # available configuration parameters
    board_size = None
    button_action = 1
    button_reset = 3
    format = '{variant}{format_board}{result}'
    format_space_empty = r'\|___\|'
    format_space_occupied = r'\|_X_\|'
    format_space_separator = ''
    variant = None

    def post_config_hook(self):
        if self.variant not in (None, 'standard', 'inverse'):
            raise ValueError('variant must be standard, inverse, or None')
        self._random_board_size = self.board_size is None
        self._random_variant = self.variant is None
        if not self._random_board_size:
            self.board_size = max(self.board_size, 3)
        self.space_format = {}
        for name in ['separator', 'occupied', 'empty']:
            value = getattr(self, f'format_space_{name}', '')
            self.space_format[name] = self.py3.safe_format(value, force_composite=True)
        self._reset()

    def _reset(self):
        if self._random_board_size:
            self.board_size = random.randint(3, 11)
        if self._random_variant:
            self.variant = random.choice(['standard', 'inverse'])
        self.cells = [False] * self.board_size
        self.index = None
        self.next_play = time.monotonic() + 1 if random.choice([True, False]) else None
        self.result = None

    def _has_treblecross(self):
        for index in range(self.board_size - 2):
            if self.cells[index] and self.cells[index + 1] and self.cells[index + 2]:
                return True
        return False

    def _makes_treblecross(self, index):
        self.cells[index] = True
        has_treblecross = self._has_treblecross()
        self.cells[index] = False
        return has_treblecross

    def _update_result(self, result):
        if self._has_treblecross():
            self.result = result
            self.next_play = None
            self.index = None
            return True
        return False

    def _play_computer_turn(self):
        empty_indexes = [index for index, occupied in enumerate(self.cells) if not occupied]
        if not empty_indexes:
            return
        if self.variant == 'standard':
            preferred_indexes = [x for x in empty_indexes if self._makes_treblecross(x)]
        else:
            preferred_indexes = [x for x in empty_indexes if not self._makes_treblecross(x)]
        index = random.choice(preferred_indexes or empty_indexes)
        self.cells[index] = True

    def _get_board(self):
        data = []
        for index, occupied in enumerate(self.cells):
            if index and self.space_format['separator']:
                data.extend(self.space_format['separator'])

            cell = self.space_format['occupied'] if occupied else self.space_format['empty']
            for part in cell:
                part = part.copy()
                part['index'] = index
                data.append(part)

        return self.py3.composite_create(data)

    def treblecross(self):
        index = self.index
        if index is not None and 0 <= index < self.board_size and not self.cells[index]:
            self.cells[index] = True
            result = 'win' if self.variant == 'standard' else 'lose'
            if not self._update_result(result):
                self.next_play = time.monotonic() + 1

        if (
            self.result is None
            and self.next_play is not None
            and time.monotonic() >= self.next_play
        ):
            self._play_computer_turn()
            result = 'lose' if self.variant == 'standard' else 'win'
            if not self._update_result(result):
                self.next_play = None

        self.index = None
        cache_until = self.py3.CACHE_FOREVER
        if self.next_play is not None:
            cache_until = self.py3.time_in(max(self.next_play - time.monotonic(), 0))

        game_data = {
            'variant': self.variant.title(),
            'format_board': self._get_board(),
            'result': f"{self.result.upper()}" if self.result else '',
        }

        return {
            'cached_until': cache_until,
            'full_text': self.py3.safe_format(self.format, game_data),
        }

    def on_click(self, event):
        button = event['button']
        if button == self.button_action:
            index = event.get('index')
            if (
                self.result is None
                and self.next_play is None
                and index is not None
                and 0 <= index < self.board_size
                and not self.cells[index]
            ):
                self.index = index
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
