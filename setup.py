"""
py3status
"""

import os
import sys
from setuptools import find_packages, setup
from setuptools.command.develop import develop
from setuptools.command.install import install
from setuptools.command.easy_install import _to_ascii, ScriptWriter

module_path = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), 'py3status')
sys.path.insert(0, module_path)
from version import version  # noqa
sys.path.remove(module_path)


# setuptools causes scripts to run slowly see
# https://github.com/pypa/setuptools/issues/510
# We can make py3-cmd run much faster when installed via
# python setup install/develop
PY3_CMD_SCRIPT_TEXT = u"""{}
# -*- coding: utf-8 -*-
import re
import sys

from py3status.command import send_command

if __name__ == '__main__':
    sys.argv[0] = re.sub(r'(-script\.pyw?|\.exe)?$', '', sys.argv[0])
    sys.exit(send_command())
"""


def install_py3_cmd(installer):
    """Attempt to overwrite /bin/py3-cmd with efficient version"""
    py_cmd = ScriptWriter.get_header()
    script_text = PY3_CMD_SCRIPT_TEXT.format(py_cmd)
    try:
        installer.write_script('py3-cmd', _to_ascii(script_text), 'b')
    except AttributeError:
        # building wheel etc
        pass


class PostDevelopCommand(develop):
    """Post-installation for develop"""

    def run(self):
        develop.run(self)
        install_py3_cmd(self)


class PostInstallCommand(install):
    """Post-installation for install"""

    def run(self):
        install.run(self)
        install_py3_cmd(self)


# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name='py3status',
    version=version,
    author='Ultrabug',
    author_email='ultrabug@ultrabug.net',
    description='py3status: an extensible i3status wrapper written in python',
    long_description=read('README.rst'),
    extras_require={'gevent': ['gevent >= 1.1']},
    url='https://github.com/ultrabug/py3status',
    download_url='https://github.com/ultrabug/py3status/tags',
    license='BSD',
    platforms='any',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[],
    cmdclass={
        'develop': PostDevelopCommand,
        'install': PostInstallCommand,
    },
    entry_points={
        'console_scripts': [
            'py3status = py3status:main',
            'py3-cmd = py3status.command:send_command',
        ]
    },
    classifiers=[
        'License :: OSI Approved :: BSD License',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ], )
