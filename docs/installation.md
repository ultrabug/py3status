# Installation

## Alpine Linux
```bash
$ apk add py3status
```

## Arch Linux
```bash
$ pacman -S py3status
```
```bash
# Real-time updates from master branch
$ yay -S py3status-git
```

## Debian & Ubuntu
```bash
$ apt-get install py3status
```
```bash
$ pip install py3status
```
/// note
If you want to use pip, you should consider using **pypi-install** from
the **python-stdeb** package (which will create a .deb out from a python
package) instead of directly calling pip.
///


## Fedora
```bash
$ dnf install py3status
```

## Gentoo Linux
```bash
# Check available USE flags if you need them.
$ emerge -a py3status
```

## NixOS
To have py3status globally persistent add to your NixOS configuration file
py3status as a Python 3 package with:
```nix
(python3Packages.py3status.overrideAttrs (oldAttrs: {
  propagatedBuildInputs = with python3Packages;[ pytz tzlocal ] ++ oldAttrs.propagatedBuildInputs;
}))
```

If you are using [i3wm](https://i3wm.org/), you
might want a section in your `/etc/nixos/configuration.nix` that looks
like this:
```nix
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
$ nix-env -iA nixpkgs.python3Packages.py3status
```

## PyPi
```bash
$ pip install py3status
```

Optional extras:
```bash
{{ install_extras() }}
```

## Void Linux
```bash
$ xbps-install -S py3status
```
