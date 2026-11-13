# Py3 API Reference

## Py3 Helper

The `Py3` helper is injected into every py3status module as `self.py3`.
It provides the shared functionality modules need to interact with
py3status, including formatting output, running commands, scheduling
updates, reading storage, reporting errors, and working with thresholds.
Use these helpers instead of duplicating core behavior inside a module.

///note
Module authors should treat **underscore**-prefixed methods and attributes as private implementation details.
///

::: py3status.py3.Py3
    options:
      filters: ["!^_"]
      show_bases: false

## Exceptions

`Py3.request()` raises a `RequestException` subclass on failure; module
code can catch the specific subclass or `RequestException` itself to
catch any of them. All Py3 exceptions derive from `Py3Exception`.

::: py3status.exceptions
    options:
      show_bases: true
