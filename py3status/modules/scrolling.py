# -*- coding: utf-8 -*-

class Py3status:
    limit = 10
    infinite_scroll = False

    class Meta:
        container = True

    def post_config_hook(self):
        self.index = 0
        self.prepend_space_to_next = False

    def _get_full_length(self):
        return sum(len(output['full_text']) + 1 for item in self.items for output in self.py3.get_output(item))

    def _cut(self, item):
        will_prepend = self.prepend_space_to_next
        if self.index == self.last_ended_at + len(item['full_text']):
            self.prepend_space_to_next = True
        else:
            self.prepend_space_to_next = False
        full_text = item['full_text'][(max(0, self.index-self.last_ended_at)):][:max(0, self.limit - self.len_so_far)]
        self.len_so_far += len(full_text)
        self.last_ended_at += len(item['full_text'])
        if self.len_so_far + 1 == self.limit:
            self.len_so_far += 1
            self.last_ended_at += 1
        elif len(full_text) > 0:
            self.len_so_far += 1
            self.last_ended_at += 1
        return {
            **item,
            'full_text': " " + full_text if will_prepend else full_text,
            'separator': True
        }

    def scrolling_frame(self):
        self.prepend_space_to_next = False
        if self._get_full_length() <= self.limit:
            self.index = 0
        self.len_so_far = 0
        self.last_ended_at = 0
        print('index', self.index)

        composite = [self._cut(output) for item in self.items for output in self.py3.get_output(item)]
        if self.infinite_scroll and self.len_so_far < self.limit:
            composite += [self._cut(output) for item in self.items for output in self.py3.get_output(item)]

        if self.infinite_scroll:
            self.index = self.index % (self._get_full_length() - 1)
            self.index += 1
        else:
            self.index += 1
            self.index = self.index % (self._get_full_length() - self.limit)

        return {
            'composite':  composite
        }