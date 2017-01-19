"""
py3status
"""

import os
import sys
from setuptools import find_packages, setup

module_path = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), 'py3status')
sys.path.insert(0, module_path)
from version import version  # noqa
sys.path.remove(module_path)


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
    url='https://github.com/ultrabug/py3status',
    download_url='https://github.com/ultrabug/py3status/tags',
    license='BSD',
    platforms='any',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[],
    entry_points={
        'console_scripts': [
            'py3status = py3status:main',
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
        'Topic :: Software Development :: Libraries :: Python Modules',
    ], )
