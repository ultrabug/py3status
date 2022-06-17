# Installation

## Arch Linux

Stable updates, official releases:

```bash
$ pacman -S py3status
```

Real-time updates from master branch:

```bash
$ yay -S py3status-git
```

## Debian & Ubuntu

Stable updates. In testing and unstable, and soon in stable backports:

```bash
$ apt-get install py3status
```

Buster users might want to check out issue #1916 and use pip3 instead or the alternative method proposed until [this debian bug](https://bugs.debian.org/890329) is handled and stable.

!!! note
    If you want to use pip, you should consider using *pypi-install* from
    the *python-stdeb* package (which will create a .deb out from a python
    package) instead of directly calling pip.

```bash
$ pip3 install py3status
```

## Fedora

```bash
$ dnf install py3status
```

## Gentoo Linux

Check available USE flags if you need them!

```bash
$ emerge -a py3status
```

## Alpine Linux

Currently available on Edge version of Alpine. Make sure you enabled the community repository, then:

```bash
$ apk add py3status
```

## PyPi

```bash
$ pip install py3status
```

There are optional requirements that you could find useful:

- `py3status[gevent]` for gevent support.
- `py3status[udev]` for udev support.

Or if you want everything:

- `py3status[all]` to install all core extra requirements and features.

## Void Linux

```bash
$ xbps-install -S py3status
```

## NixOS

To have py3status globally persistent add to your NixOS configuration file
py3status as a Python 3 package with:

```
(python3Packages.py3status.overrideAttrs (oldAttrs: {
  propagatedBuildInputs = with python3Packages;[ pytz tzlocal ] ++ oldAttrs.propagatedBuildInputs;
}))
```

If you are, and you probably are, using [i3](https://i3wm.org/) you
might want a section in your `/etc/nixos/configuration.nix` that looks
like this:

```
{
  services.xserver.windowManager.i3 = {
    enable = true;
    extraPackages = with pkgs; [
      dmenu
      i3status
      i3lock
      (python3Packages.py3status.overrideAttrs (oldAttrs: {
        propagatedBuildInputs = with python3Packages; [ pytz tzlocal ] ++ oldAttrs.propagatedBuildInputs;
      }))
    ];
  };
}
```

In this example I included the python packages **pytz** and **tzlocal**
which are necessary for the py3status module **clock**. The default
packages that come with i3 (dmenu, i3status, i3lock) have to be
mentioned if they should still be there.

```bash
$ nix-env -i python3.6-py3status
```
