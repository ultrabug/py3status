#!/bin/bash

if [ ! -f py3status/py3status.py ]; then
	echo "py3status/py3status.py not found, run me from the cloned directory"
	exit 1
fi

echo -n "setting up symlink... "
if [ ! -L /usr/bin/py3status ]; then
	ln -s $(pwd)/py3status/py3status.py /usr/bin/py3status || exit 2
fi
echo "ok"

echo -n "setting up permissions... "
chmod +x py3status/py3status.py || exit 3
echo "ok"

echo "setup done, enjoy !"
