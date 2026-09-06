# Developing and Contributing

Contributions to Py3status including documentation, the core code, or
for new or existing modules are very welcome.

* Please read carefully the zen describing the minimal things to keep in
mind when contributing or participating to this project.

* Feel free to open an [GitHub issue](https://github.com/ultrabug/py3status/issues)
to propose your ideas as request for comments **`[RFC]`** and to join us in
`#py3status` on [OFTC](https://www.oftc.net) for a live chat. Open in your browser
https://webchat.oftc.net/?channels=py3status or, with an IRC client
```
/connect irc.oftc.net
/join #py3status
```

* To make a contribution, please create a [GitHub pull request](https://github.com/ultrabug/py3status/pulls).

* Any functional change should be done via pull requests, even by people
with push access.

* Each PR requires at least one approval from project maintainers before a
PR can be merged.

## Zen of Py3status

**efficient and simple defaults**

> We like Py3status because it's a drop-in replacement of i3status. i3
> users don't expect fancy and magical things, they use i3 because it's
> simple and efficient. Keep configuration options and default formats
> as simple as possible

**it's not because you can that you should**

> On modules, expose things that you WILL use, not things that you COULD
> use. On core, make features and options as seamless as possible (lazy
> loading) with sane defaults and no mandatory requirements.

**good enough is good enough**

> Strive for and accept "good enough" features / proposals. We shall
> refrain from refining indefinitely.

**one feature/idea at a time**

> Trust and foster iteration with your peers by refraining from
> digressions. Keep discussions focused on the initial topic and easy to
> get into. Proposals should not contain multiple features or
> corrections at once.

**modules are responsible for user information and interactions**

> That is what's written in the bar and its behavior on clicks etc.

**core is responsible for user experience**

> Core features and configuration options should focus on user
> experience. Things that are related to the general output of the bar
> are handled by core. Smart things overlaying modules (such as
> standardized options) should also end up in the core.

**rely on i3status color scheme**

> No fancy colors by default, only i3status good/degraded/bad. If we
> want to provide enhanced coloring, this should be through a core
> feature such as thresholds.

**rely on the i3bar protocol**

> what's possible with it, we should support and offer.

## What you will need

- `python` <https://www.python.org>
- `i3status` <https://i3wm.org/i3status>
- `hatch` <https://hatch.pypa.io>

`hatch` manages everything else (pytest, ruff, black, isort, the docs
toolchain) as isolated environments - you don't need to install those
individually.

## Setting up a development environment


```bash
# First, clone the git repository using https or ssh
$ git clone https://github.com/ultrabug/py3status.git  # https
$ git clone git@github.com:ultrabug/py3status.git  # ssh (needs github account)

# cd to the py3status directory
$ cd py3status

# you may not need to use sudo to install
$ pip install -e .
```

you can now run Py3status and any changes to the code you make will be
available after a reload.

## Documentation

Documentation pages are located under the docs/ folder.

To run the documentation site locally (useful for previewing changes), use:
```bash
$ hatch run docs:serve
```

## Testing with hatch

Py3status uses hatch for testing. All submissions to the project must pass
testing.

Run the test suite:
```bash
$ hatch run test:test
```

Run style checks (ruff, black, isort):
```bash
$ hatch run style:check
```

Or run both at once:
```bash
$ hatch run all
```

Tests are kept in the `tests` directory.

## Github Actions

When you create your Pull Request, checks from the Github Actions CI will
automatically run.

If something fails in the CI:

- Take a look the build log
- If you don't get what is failing or why it is failing, feel free to
  tell it as a comment in your PR: people here are helpful and
  open-minded :)
- Once the problem is identified and fixed, rebase your commit with
  the fix and push it on your fork to trigger the CI again

## Coding in containers

Some distributions or installations may grant i3status `CAP_NET_ADMIN`, which is required
for certain network-related functionality such as reporting link speed. This capability may
be unavailable in containers.

Check whether i3status has the capability:
```bash
$ getcap "$(command -v i3status)"
/usr/sbin/i3status = cap_net_admin+ep
```

If you don't need this functionality, you can remove the capability:
```bash
$ sudo setcap -r "$(command -v i3status)"
```

## Profiling Py3status

A small tool to measure `py3status` performance between changes and
allows testing of old versions, etc. It's a little clunky but it does
the job. <https://github.com/tobes/py3status-profiler>
```
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
```
