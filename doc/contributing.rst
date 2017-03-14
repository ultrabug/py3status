Contributing
============

Contributions to py3status either to the core code or for new or
existing modules are welcome.

What you will need
------------------

- python3/python2
- i3status
    - http://i3wm.org/i3status/
    - https://github.com/i3/i3status
- pytest pytest-flake8
    - https://pypi.python.org/pypi/pytest
    - https://pypi.python.org/pypi/pytest-flake8

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
