# basestring does not exist in python3
try:
    basestring
except NameError:
    basestring = str


class Composite:
    """
    Helper class to identify a composite and store its content
    A Composite is essentially a wrapped list containing response items.
    """

    def __init__(self, content=None):
        # try and create a composite from various input types
        if content is None:
            content = []
        elif isinstance(content, Composite):
            content = content.get_content()[:]
        elif isinstance(content, dict):
            content = [content]
        elif isinstance(content, basestring):
            content = [{"full_text": content}]

        assert isinstance(content, list)
        self._content = content

    def __repr__(self):
        return u"<Composite {}>".format(self._content)

    def __len__(self):
        return len(self._content)

    def __getitem__(self, key):
        if isinstance(key, slice):
            return Composite(self._content[key])
        return self._content[key]

    def __setitem__(self, key, value):
        self._content[key] = value

    def __delitem__(self, key):
        del self._content[key]

    def __iter__(self):
        return iter(self._content)

    def __iadd__(self, other):
        self.append(other)
        return self

    def copy(self):
        """
        Return a shallow copy of the Composite
        """
        return Composite([x.copy() for x in self._content])

    def append(self, item):
        """
        Add an item to the Composite.  Item can be a Composite, list etc
        """
        if isinstance(item, Composite):
            self._content += item.get_content()
        elif isinstance(item, list):
            self._content += item
        elif isinstance(item, dict):
            self._content.append(item)
        elif isinstance(item, basestring):
            self._content.append({"full_text": item})
        else:
            msg = "{!r} not suitable to append to Composite"
            raise Exception(msg.format(item))

    def get_content(self):
        """
        Retrieve the contained list
        """
        return self._content

    def text(self):
        """
        Return the text only component of the composite.
        """
        return "".join([x.get("full_text", "") for x in self._content])

    def simplify(self):
        """
        Simplify the content of a Composite merging any parts that can be
        and returning the new Composite as well as updating itself internally
        """
        final_output = []
        diff_last = None
        item_last = None
        for item in self._content:
            # remove any undefined colors
            if hasattr(item.get("color"), "none_setting"):
                del item["color"]
            # ignore empty items
            if not item.get("full_text") and not item.get("separator"):
                continue
            # merge items if we can
            diff = item.copy()
            del diff["full_text"]

            if diff == diff_last or (item["full_text"].strip() == "" and item_last):
                item_last["full_text"] += item["full_text"]
            else:
                diff_last = diff
                item_last = item.copy()  # copy item as we may change it
                final_output.append(item_last)
        self._content = final_output
        return self

    @staticmethod
    def composite_join(separator, items):
        """
        Join a list of items with a separator.
        This is used in joining strings, responses and Composites.
        The output will be a Composite.
        """
        output = Composite()
        first_item = True
        for item in items:
            # skip empty items
            if not item:
                continue
            # skip separator on first item
            if first_item:
                first_item = False
            else:
                output.append(separator)
            output.append(item)
        return output

    @staticmethod
    def composite_update(item, update_dict, soft=False):
        """
        Takes a Composite (item) and updates all entries with values from
        update_dict.  Updates can be soft in which case existing values are not
        overwritten.

        If item is of type string it is first converted to a Composite
        """
        item = Composite(item)

        for part in item.get_content():
            if soft:
                for key, value in update_dict.items():
                    if key not in part:
                        part[key] = value
            else:
                part.update(update_dict)
        return item
