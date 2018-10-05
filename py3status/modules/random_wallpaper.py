# -*- coding: utf-8 -*-
"""
Allows you to change your background image (i.e. wallpaper).

This module sets a random wallpaper each time you start py3status. Additionally,
you can request a change by clicking on it.

Configuration parameters:
    button_next: Select the button used to set the wallpaper as the next in the
        list. (default 1)
    button_prev: Select the button used to set the wallpaper as the previous in
        the list. (default 3)
    button_rand: Select the button used to set a random wallpaper in the list.
        (default 2)
    cache_list: Set to True to cache the list of images. This will result in a
        faster and less power-consuming module, but you will need to reload the
        module in order to update the list of images. (default False)
    feh_args: The arguments that will be given to feh. (default '--bg-scale')
    filter_extensions: The list of extensions that will be allowed for the
        wallpapers. Set to None to authorize all extensions. (default ['jpg'])
    first_image_path: Path to the first image to be loaded. This page should be
        in the list of found wallpapers for this module to work properly. If
        set to None, a random image will be used. (default None)
    format_string: content that will be printed on the i3bar.
        (default 'Wallpaper {current_basename}')
    ignore_files: List of filename to ignore when searching for wallpapers.
        (default [])
    recursive_search: Set to True to search for images in subdirectories.
        (default False)
    search_dirs: The list of directories to search for wallpapers.
        (default ['~/Pictures/'])
    unique_basename: Set to true in order to filter images by their basename
        (i.e. compare without the extension). (default False)

Button reference: (see the official py3status reference if unsure, this might be
    outdated)
    1: left click
    2: middle click
    3: right click
    4: scroll up
    5: scroll down

Format placeholders:
    {current_name} Full name (including path) of the current wallpaper
    {current_basename} Basename (i.e. excluding path) of the current wallpaper

Requires:
    feh Used to set the background image.

Author: rchaput <rchaput.pro@gmail.com>

License: Apache License 2.0 <https://www.apache.org/licenses/LICENSE-2.0.html>
"""

import subprocess
import os
from random import randint


class Py3status:

    # Public attributes (i.e. config parameters)
    button_next = 1
    button_prev = 3
    button_rand = 2
    cache_list = False
    feh_args = '--bg-scale'
    filter_extensions = [
        'jpg'
    ]
    first_image_path = None
    format_string = 'Wallpaper {current_basename}'
    ignore_files = []
    recursive_search = False
    search_dirs = [
        '~/Pictures/'
    ]
    unique_basename = False

    def show(self):
        """
        Main method, returns the module content to py3status.
        Note that this is the only public method (non-special, unlike on_click
        and post_config_hook), and, as such, this is the method that py3status
        will automatically call.
        """
        if self.__feh is None:
            full_text = "Error! Feh not found"
        else:
            data = {'current_name': self.__current_name,
                    'current_basename': os.path.basename(self.__current_name)}
            full_text = self.py3.safe_format(self.format_string, data)
        return {
            'full_text': full_text,
            'cached_until': self.py3.CACHE_FOREVER
        }

    def on_click(self, event):
        """
        Callback function, called when a click event is received.
        """
        # {'y': 13,'x': 1737, 'button': 1, 'name':'example','instance':'first'}
        if not self.cache_list:
            self.__wallpapers = self.__find_wallpapers()
        index = self.__current_index
        if event['button'] == self.button_next:
            index = (index + 1) % len(self.__wallpapers)
        elif event['button'] == self.button_prev:
            index = (index - 1) % len(self.__wallpapers)
        elif event['button'] == self.button_rand:
            index = randint(0, len(self.__wallpapers) - 1)
        if index != self.__current_index:
            self.__current_index = index
            self.__set_wallpaper(self.__wallpapers[self.__current_index])

    def post_config_hook(self):
        """
        Initialization method (after config parameters have been set).
        """
        self.__feh = self.__find_feh()
        if self.__feh is None:
            return
        self.__wallpapers = self.__find_wallpapers()
        if self.first_image_path is None:
            # get random index
            self.__current_index = randint(0, len(self.__wallpapers) - 1)
        else:
            # get index of given path
            try:
                self.__current_index = \
                    self.__wallpapers.index(self.first_image_path)
            except ValueError:
                self.__log_warning("Tried to force first image but path %s was"
                                   "not found in the list of wallpapers"
                                   % self.first_image_path)
                self.__current_index = 0
        self.__set_wallpaper(self.__wallpapers[self.__current_index])

    # Private Methods

    def __init__(self):
        # __feh = path to the feh executable
        self.__feh = None
        # __wallpapers = list of found (and suitable) wallpapers
        self.__wallpapers = None
        # __current_name = path to the currently loaded wallpaper
        self.__current_name = None
        # __current_index = index of the current wallpaper (in __wallpapers)
        self.__current_index = None

    def __find_feh(self):
        """
        Returns the path to the feh executable, or None if feh is not found.
        """
        process = subprocess.Popen(['which', 'feh'], stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        process.wait()
        code = process.returncode
        if code != 0:
            err = process.stderr.read()
            self.__log_error("Could not find feh: %d %s" % (code, err))
            return None  # Error
        else:
            result = process.stdout.read()[:-1]
            # The last character is '\n'
            return result

    def __find_wallpapers(self):
        """
        Returns an array containing the paths to the wallpapers found in the
        specified directories.
        """
        wallpapers = list()
        for dirpath in self.search_dirs:
            self.__find_wallpapers_in_dir(wallpapers, dirpath)
        return wallpapers

    def __find_wallpapers_in_dir(self, wallpapers, dirpath):
        """
        Adds the files in the given directory to wallpapers.
        wallpapers = an initialized list (potentially modified)
        dirpath = Path to the directory that will be explored. This path will
        be expanded using expanduser so '~' is authorized.
        """
        dirpath = os.path.expanduser(dirpath)
        for root, dirs, files in os.walk(dirpath, topdown=True):
            # del dirs[:] # delete the list of dirs, cancelling the recursion
            # files is the array of files in the tree
            if not self.recursive_search:
                dirs.clear()
            wallpapers.extend(
                [os.path.join(root, x) for x in files
                 if self.__should_add_file(wallpapers, x)])

    def __should_add_file(self, wallpapers, filename):
        """
        Determines if the given filename should be added to the list of
        wallpapers (i.e. if the extension is correct and the basename is unique)
        """
        return self.__is_extension_correct(filename) \
            and self.__is_unique_basename(wallpapers, filename) \
            and not self.__is_ignored_file(filename)

    def __is_extension_correct(self, filename):
        """
        Determines if the given filename has a correct extension.
        In particular, returns True if self.filter_extensions == None
        or if self.filter_extensions contains the extension of filename
        (e.g. jpg, png,...)
        Please note that filename can be an absolute or relative path, or even
        a basename (i.e. no path)
        """
        if self.filter_extensions is None:
            return True
        # splitext('/file.ext') returns ('/file', '.ext')
        # Thus [1] returns the 2nd value (i.e. the extension) '.ext'
        # And [1:] deletes the heading '.' in the extension 'ext'
        extension = os.path.splitext(filename)[1][1:]
        return extension in self.filter_extensions

    def __is_unique_basename(self, wallpapers, filename):
        """
        Determines if a basename (i.e. a filename without extension) is unique
        in the given list of files.
        If self.unique_basename is False, no filter will be done on filenames
        and this method will returns True each call.
        """
        if not self.unique_basename:
            return True
        basename = os.path.basename(filename)
        for x in wallpapers:
            x_basename = os.path.basename(x)
            if basename == x_basename:
                return False
        return True

    def __is_ignored_file(self, filename):
        if self.ignore_files is None:
            return False
        else:
            return filename in self.ignore_files

    def __set_wallpaper(self, path):
        """
        Changes the current wallpaper.
        Requires self.__feh to be not-None and path to be a correct path to an
        image that feh can handle.
        Returns the error code from feh or -1 if either __feh or path is None
        """
        if self.__feh is None:
            self.__log_error("Cannot set wallpaper if feh is not found")
            return -1
        elif path is None:
            self.__log_error("Cannot set wallpaper: path is not defined")
            return -1
        else:
            self.__log_info("Trying to set wallpaper: %s" % path)
            process = subprocess.Popen([self.__feh, self.feh_args, path],
                                       stderr=subprocess.PIPE)
            process.wait()
            code = process.returncode
            if code == 0:
                self.__log_info("Wallpaper set successfully.")
                self.__current_name = path
            else:
                err = process.stderr.read()
                self.__log_error("Could not set wallpaper, feh returned error"
                                 "code %d and message %s" % (code, err))
            return code

    def __log_error(self, msg):
        """
        Logs an error. Uses the py3 helper.
        Convenience method for self.py3.log(msg, self.py3.LOG_ERROR)
        """
        self.py3.log(msg, self.py3.LOG_ERROR)

    def __log_warning(self, msg):
        """
        Logs a warning. Uses the py3 helper.
        Convenience method for self.py3.log(msg, self.py3.LOG_WARNING)
        """
        self.py3.log(msg, self.py3.LOG_WARNING)

    def __log_info(self, msg):
        """
        Logs an information. Uses the py3helper.
        Convenience method for self.py3.log(msg, self.py3.LOG_INFO)
        """
        self.py3.log(msg, self.py3.LOG_INFO)


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    config = {
        'recursive_search': True
    }
    from py3status.module_test import module_test

    module_test(Py3status, config=config)
