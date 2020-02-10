.. _contributing:

Developing and Contributing
===========================

Contributions to py3status including documentation, the core code, or for
new or existing modules are very welcome.

Please read carefully the :ref:`zen` describing the minimal things
to keep in mind when contributing or participating to this project.

Feel free to open an issue to propose your ideas as request for comments [RFC]
and to join us on IRC Freenode #py3status channel for a live chat.

.. _zen:

Zen of py3status
----------------

efficient and simple defaults
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    We like py3status because it's a drop-in replacement of i3status.
    i3 users don't expect fancy and magical things, they use i3 because it's
    simple and efficient.
    Keep configuration options and default formats as simple as possible

it's not because you can that you should
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    On modules, expose things that you WILL use, not things that you COULD use.
    On core, make features and options as seamless as possible (lazy loading)
    with sane defaults and no mandatory requirements.

good enough is good enough
^^^^^^^^^^^^^^^^^^^^^^^^^^

    Strive for and accept "good enough" features / proposals.
    We shall refrain from refining indefinitely.

one feature/idea at a time
^^^^^^^^^^^^^^^^^^^^^^^^^^

    Trust and foster iteration with your peers by refraining from digressions.
    Keep discussions focused on the initial topic and easy to get into.
    Proposals should not contain multiple features or corrections at once.

modules are responsible for user information and interactions
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    That is what's written in the bar and its behavior on clicks etc.

core is responsible for user experience
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    Core features and configuration options should focus on user experience.
    Things that are related to the general output of the bar are handled by core.
    Smart things overlaying modules (such as standardized options) should also
    end up in the core.

rely on i3status color scheme
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    No fancy colors by default, only i3status good/degraded/bad.
    If we want to provide enhanced coloring, this should be through a core
    feature such as thresholds.

rely on the i3bar protocol
^^^^^^^^^^^^^^^^^^^^^^^^^^

    what's possible with it, we should support and offer.


What you will need
------------------

- python3
- i3status
    - https://i3wm.org/i3status/
    - https://github.com/i3/i3status
- pytest pytest-flake8
    - https://pypi.python.org/pypi/pytest
    - https://pypi.python.org/pypi/pytest-flake8
- black
    - https://pypi.org/project/black/
- tox
    - https://pypi.org/project/tox/

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

you can now run py3status and any changes to the code you make will be available
after a reload.


.. note::
    py3status will only be installed for the version of python that you used
    to run ``setup.py``.

    If you wish to have multiple versions available. First run ``setup.py
    develop`` using the required python versions. Next copy the
    executable eg ``sudo cp /usr/bin/py3status /usr/bin/py3status2`` Then
    edit the hashbang to point to your chosen python version.

Python versions
---------------

Starting with version 3.26, py3status will only run using python 3.

tox
---

Py3status uses tox for testing. All submissions to the project must pass testing.
To install these via pip use

.. code-block:: shell

    pip install pytest
    pip install pytest-flake8
    pip install tox
    pip install black  # needs python 3.6+

The tests can be run by using ``tox`` in the py3status root directory.

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

To allow it to run without these capabilities (hence disabling some of the
functionalities), remove it with:

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

Any functional change should be done via pull requests,
even by people with push access.

Each PR requires at least one approval from project maintainers
before a PR can be merged.
