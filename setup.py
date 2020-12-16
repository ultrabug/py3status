"""
py3status
"""

from setuptools import find_packages, setup
import fastentrypoints  # noqa f401
import sys
from pathlib import Path

module_path = Path(__file__).resolve().parent / "py3status"
sys.path.insert(0, str(module_path))
from version import version  # noqa e402

sys.path.remove(str(module_path))


# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    return (Path(__file__).resolve().parent / fname).read_text()


# extra requirements
req_gevent = ["gevent >= 1.1"]
req_udev = ["pyudev >= 0.21.0"]
req_all = req_gevent + req_udev

setup(
    name="py3status",
    version=version,
    author="Ultrabug",
    author_email="ultrabug@ultrabug.net",
    description="py3status: an extensible i3status wrapper written in python",
    long_description=read("README.rst"),
    long_description_content_type="text/x-rst",
    extras_require={"all": req_all, "gevent": req_gevent, "udev": req_udev},
    url="https://github.com/ultrabug/py3status",
    download_url="https://github.com/ultrabug/py3status/tags",
    license="BSD",
    platforms="any",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[],
    entry_points={
        "console_scripts": [
            "py3status = py3status:main",
            "py3-cmd = py3status.command:send_command",
        ]
    },
    python_requires=">=3.6",
    classifiers=[
        "License :: OSI Approved :: BSD License",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3 :: Only",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
