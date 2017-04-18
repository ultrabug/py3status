# What you will need

- python3
- i3status
    - http://i3wm.org/i3status/
    - https://github.com/i3/i3status
- flake8
    - https://pypi.python.org/pypi/flake8
    - https://github.com/PyCQA/flake8

# Flake 8

Before making any Pull Request, make sure that flake8 tests pass without any
error/warning:

- Code what you want to
- Run `flake8 .` at the root of the repository
- Fix potential errors/warnings
- If you already commited your code, make sure to amend (`git commit --amend`)
  or rebase your commit with the flake8 fixes !

# Travis CI

When you create your Pull Request, some checks from Travis CI will
automatically run; you can see [previous
builds](https://travis-ci.org/ultrabug/py3status/) if you want to.

If something fails in the CI:

- Take a look the build log
- If you don't get what is failing or why it is failing, feel free to tell it
  as a comment in your PR: people here are helpful and open-minded :)
- Once the problem is identified and fixed, rebase your commit with the fix and
  push it on your fork to trigger the CI again

For reference, you can take a look at [this
PR](https://github.com/ultrabug/py3status/pull/193); you won't see the old
failed CI runs, but you'll get an idea of the PR flow.

# Coding in containers

Warning, by default (at least [on
Archlinux](https://projects.archlinux.org/svntogit/community.git/tree/trunk/i3status.install?h=packages/i3status#n2)),
i3status has cap\_net\_admin capabilities, which will make it fail with
`operation not permitted` when running inside a Docker container.

```
$ getcap `which i3status`
/usr/sbin/i3status = cap_net_admin+ep
```

To allow it to run without these capabilites (hence disabling some of the
functionnalities), remove it with:

```
setcap -r `which i3status`
```

