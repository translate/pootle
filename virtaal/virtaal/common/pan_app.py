#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2007-2008 Zuza Software Foundation
#
# This file is part of Virtaal.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.

import ConfigParser
import logging
import os
import sys
import locale, gettext
locale.setlocale(locale.LC_ALL)
gettext.install("virtaal", unicode=1)
from translate.misc import file_discovery
from translate.lang import data

from virtaal.__version__ import ver

DEBUG = True # Enable debugging by default, while bin/virtaal still disables it by default.
             # This means that if Virtaal (or parts thereof) is run in some other strange way,
             # debugging is enabled.


x_generator = 'Virtaal ' + ver
default_config_name = "virtaal.ini"

def get_config_dir():
    if os.name == 'nt':
        confdir = os.path.join(os.environ['APPDATA'], 'Virtaal')
    else:
        confdir = os.path.expanduser('~/.virtaal')

    if not os.path.exists(confdir):
        os.makedirs(confdir)

    return confdir

def osx_lang():
    """Do some non-posix things to get the language on OSX."""
    import CoreFoundation
    return CoreFoundation.CFLocaleCopyPreferredLanguages()[0]

def get_locale_lang():
    #if we wanted to determine the UI language ourselves, this should work:
    #lang = locale.getdefaultlocale(('LANGUAGE', 'LC_ALL', 'LC_MESSAGES', 'LANG'))[0]
    #if not lang and sys.platform == "darwin":
    #   lang = osx_lang()

    # guess default target lang based on locale, simplify to commonly used form
    try:
        lang = locale.getdefaultlocale(('LANGUAGE', 'LC_ALL', 'LANG'))[0]
        if not lang and sys.platform == "darwin":
           lang = osx_lang()
        if lang and _(''):
            return data.simplify_to_common(lang)
    except Exception:
        logging.exception("Could not get locale")
    return 'en'

def name():
    # pwd is only available on UNIX
    try:
        import pwd
        import getpass
    except ImportError, _e:
        return u""
    return pwd.getpwnam(getpass.getuser())[4].split(",")[0]

def get_default_font():
    default_font = 'monospace'
    font_size = ''

    # First try and get the default font size from GConf
    try:
        import gconf
        client = gconf.client_get_default()
        client.add_dir('/desktop/gnome/interface', gconf.CLIENT_PRELOAD_NONE)
        font_name = client.get_string('/desktop/gnome/interface/monospace_font_name')
        font_size = font_name.split(' ')[-1]
    except ImportError, ie:
        logging.debug('Unable to import gconf module: %s', ie)
    except Exception:
        # Ignore any other errors and try the next method
        pass

    # Get the default font size from Gtk
    if not font_size:
        import gtk
        font_name = str(gtk.Label().rc_get_style().font_desc)
        font_size = font_name.split(' ')[-1]

    if font_size:
        default_font += ' ' + font_size

    return default_font

defaultfont = get_default_font()


class Settings:
    """Handles loading/saving settings from/to a configuration file."""

    sections = ["translator", "general", "language", "placeable_state", "plugin_state", "undo"]

    translator =    {
        "name": name(),
        "email": "",
        "team": "",
    }
    general =       {
        "lastdir": "",
        "windowwidth": 796,
        "windowheight": 544,
    }
    language =      {
        "nplurals": 0,
        "plural": None,
        "recentlangs": "",
        "sourcefont": defaultfont,
        "sourcelang": "en",
        "targetfont": defaultfont,
        "targetlang": None,
    }
    placeable_state = {
        "altattrplaceable": "disabled",
        "fileplaceable": "disabled",
    }
    plugin_state =  {
        "_helloworld": "disabled",
    }
    undo = {
        "depth": 10000,
    }

    def __init__(self, filename = None):
        """Load settings, using the given or default filename"""
        if not filename:
            self.filename = os.path.join(get_config_dir(), default_config_name)
        else:
            self.filename = filename
            if not os.path.isfile(self.filename):
                raise Exception

        self.language["targetlang"] = data.simplify_to_common(get_locale_lang())
        self.config = ConfigParser.RawConfigParser()
        self.read()

    def read(self):
        """Read the configuration file and set the dictionaries up."""
        self.config.read(self.filename)
        for section in self.sections:
            if not self.config.has_section(section):
                self.config.add_section(section)

        for key, value in self.config.items("translator"):
            self.translator[key] = value
        for key, value in self.config.items("general"):
            self.general[key] = value
        for key, value in self.config.items("language"):
            self.language[key] = value
        for key, value in self.config.items("placeable_state"):
            self.placeable_state[key] = value
        for key, value in self.config.items("plugin_state"):
            self.plugin_state[key] = value
        for key, value in self.config.items("undo"):
            self.undo[key] = value

        # Make sure we have some kind of font names to work with
        for font in ('sourcefont', 'targetfont'):
            if not self.language[font]:
                self.language[font] = defaultfont

    def write(self):
        """Write the configuration file."""

        # Don't save the default font to file
        fonts = (self.language['sourcefont'], self.language['targetfont'])
        for font in ('sourcefont', 'targetfont'):
            if self.language[font] == defaultfont:
                self.language[font] = ''

        for key in self.translator:
            self.config.set("translator", key, self.translator[key])
        for key in self.general:
            self.config.set("general", key, self.general[key])
        for key in self.language:
            self.config.set("language", key, self.language[key])
        for key in self.placeable_state:
            self.config.set("placeable_state", key, self.placeable_state[key])
        for key in self.plugin_state:
            self.config.set("plugin_state", key, self.plugin_state[key])
        for key in self.undo:
            self.config.set("undo", key, self.undo[key])

        # make sure that the configuration directory exists
        project_dir = os.path.split(self.filename)[0]
        if not os.path.isdir(project_dir):
            os.makedirs(project_dir)
        file = open(self.filename, 'w')
        self.config.write(file)
        file.close()

        self.language['sourcefont'] = fonts[0]
        self.language['targetfont'] = fonts[1]

settings = Settings()

# Determine the directory the main executable is running from
main_dir = u''
if getattr(sys, 'frozen', False):
    main_dir = os.path.dirname(unicode(sys.executable, sys.getfilesystemencoding()))
else:
    main_dir = os.path.dirname(unicode(sys.argv[0], sys.getfilesystemencoding()))

def get_abs_data_filename(path_parts, basedirs=None):
    """Get the absolute path to the given file- or directory name in Virtaal's
        data directory.

        @type  path_parts: list
        @param path_parts: The path parts that can be joined by os.path.join().
        """
    if basedirs is None:
        basedirs = []
    basedirs += [
        os.path.join(os.path.dirname(unicode(__file__, sys.getfilesystemencoding())), os.path.pardir),
    ]
    return file_discovery.get_abs_data_filename(path_parts, basedirs=basedirs)

def load_config(filename, section=None):
    """Load the configuration from the given filename (and optional section
        into a dictionary structure.

        @returns: A 2D-dictionary representing the configuration file if no
            section was specified. Otherwise a simple dictionary representing
            the given configuration section."""
    parser = ConfigParser.RawConfigParser()
    parser.read(filename)

    if section:
        if section not in parser.sections():
            return {}
        return dict(parser.items(section))

    conf = {}
    for section in parser.sections():
        conf[section] = dict(parser.items(section))
    return conf

def save_config(filename, config, section=None):
    """Save the given configuration data to the given filename and under the
        given section (if specified).

        @param config: A dictionary containing the configuration section data
            if C{section} was specified. Otherwise, if C{section} is not
            specified, it should be a 2D-dictionary representing the entire
            configuration file."""
    parser = ConfigParser.ConfigParser()
    parser.read(filename)

    if section:
        config = {section: config}

    for sect in config.keys():
        parser.remove_section(sect)

    for section, section_conf in config.items():
        if section not in parser.sections():
            parser.add_section(section)
        for key, value in section_conf.items():
            if isinstance(value, list):
                value = ','.join(value)
            parser.set(section, key, value)

    conffile = open(filename, 'w')
    parser.write(conffile)
    conffile.close()
