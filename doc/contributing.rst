Developing and Contributing
===========================

Contributions to py3status including documentation, the core code, or for
new or existing modules are welcome.

What you will need
------------------

- python3/python2
- i3status
    - http://i3wm.org/i3status/
    - https://github.com/i3/i3status
- pytest pytest-flake8
    - https://pypi.python.org/pypi/pytest
    - https://pypi.python.org/pypi/pytest-flake8

.. _setup:

Setting up a development environment
------------------------------------

First clone the git repository

.. code-block:: shell

    # using https
    git clone https://github.com/ultrabug/py3status.git

    # using ssh (needs github account)
    git clone git@github.com:ultrabug/py3status.git

Run setup.py to install

.. code-block:: shell

    # cd to the directory containing setup.py
    cd py3status

    # install you may need to use sudo to have required permissions
    python setup.py develop

you can now run py3status and any changes to the code you make will active.


.. note::
    py3status will only be installed for the version of python that you used
    to run ``setup.py``.  To run against a different version of python
    You should repeat the above step eg ``python2.7 setup.py develop``.

    If you wish to have multiple versions available. First run ``setup.py
    develop`` using the required python versions. Next copy the
    executable eg ``sudo cp /usr/bin/py3status /usr/bin/py3status2`` Then
    edit the hashbang to point to your chosen python version.

Python versions
---------------

py3status code, including modules, should run under both python 2 and python 3.

Pytest
------

Py3status uses pytest and the pytest-flake8 plugin for testing. All submissions
to the project must pass testing. To install these via pip use

.. code-block:: shell

    pip install pytest
    pip install pytest-flake8

The tests can be run by using ``py.test --flake8`` in the py3status root directory.

Tests are kept in the ``tests`` directory.

Travis CI
---------

When you create your Pull Request, some checks from Travis CI will
automatically run; you can see `previous
builds <https://travis-ci.org/ultrabug/py3status/>`_ if you want to.

If something fails in the CI:

- Take a look the build log
- If you don't get what is failing or why it is failing, feel free to tell it
  as a comment in your PR: people here are helpful and open-minded :)
- Once the problem is identified and fixed, rebase your commit with the fix and
  push it on your fork to trigger the CI again

For reference, you can take a look at `this
PR <https://github.com/ultrabug/py3status/pull/193>`_; you won't see the old
failed CI runs, but you'll get an idea of the PR flow.

Coding in containers
--------------------

Warning, by default (at least `on
Archlinux <https://projects.archlinux.org/svntogit/community.git/tree/trunk/i3status.install?h=packages/i3status#n2>`_),
i3status has cap\_net\_admin capabilities, which will make it fail with
``operation not permitted`` when running inside a Docker container.

.. code-block:: shell

    $ getcap `which i3status`
    /usr/sbin/i3status = cap_net_admin+ep

To allow it to run without these capabilites (hence disabling some of the
functionnalities), remove it with:

.. code-block:: shell

    setcap -r `which i3status`

Building documentation
----------------------

Py3status documentation is build using ``sphinx``.  The requirements
needed to build the documentation are in ``doc/doc-requirements.txt``
make sure you have them installed.

To build the documentation.

.. code-block:: shell

    # cd to the doc directory
    cd doc

    # build documentation
    make html

The created documentation will be found in ``_build/html``

Profiling py3status
-------------------

A small tool to measure ``py3status`` performance between changes and
allows testing of old versions, etc. It's a little clunky but it does
the job. https://github.com/tobes/py3status-profiler

.. code-block:: none

    # pprofile
    Running tests for 10 minutes.
    [██████████] 100.00%  10:00  (22.12)
    user 21.41s
    system 0.71s
    total 22.12s

    # vmprof
    Running tests for 10 minutes.
    [██████████] 100.00%  10:00  (2.10)
    user 1.77s
    system 0.33s
    total 2.1s

    # cprofile
    Running tests for 10 minutes.
    [██████████] 100.00%  10:00  (0.92)
    user 0.87s
    system 0.05s
    total 0.92

Contributions
-------------

To make a contribution please create a
`pull request <https://github.com/ultrabug/py3status/pulls>`_.
