#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008-2009 Zuza Software Foundation
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

"""Plugin to import data from other applications.

Currently there is some support for importing settings from Poedit and
Lokalize. Translation Memory can be imported from Poedit and Lokalize.
"""

import bsddb
import ConfigParser
import logging
import os
import StringIO
import struct
from os import path
try:
    from sqlite3 import dbapi2
except ImportError:
    from pysqlite2 import dbapi2

from virtaal.common import pan_app
from virtaal.controllers import BasePlugin

from translate.storage.pypo import extractpoline
from translate.storage import tmdb


def _prepare_db_string(string):
    """Helper method needed by the Berkeley DB TM converters."""
    string = '"%s"' % string
    string = unicode(extractpoline(string), 'utf-8')
    return string

class Plugin(BasePlugin):
    description = _('Migrate settings from KBabel, Lokalize and/or Poedit to Virtaal.')
    display_name = _('Migration Assistant')
    version = 0.1

    default_config = {
        "tmdb": path.join(pan_app.get_config_dir(), "tm.db")
    }

    def __init__(self, internal_name, main_controller):
        self.internal_name = internal_name
        self.main_controller = main_controller
        self.load_config()
        self._init_plugin()

    def _init_plugin(self):
        message = _('Should Virtaal try to import settings and data from other applications?')
        must_migrate = self.main_controller.show_prompt(_('Import data from other applications?'), message)
        if not must_migrate:
            logging.debug('Migration not done due to user choice')
        else:
            # We'll store the tm here:
            self.tmdb = tmdb.TMDB(self.config["tmdb"])
            # We actually need source, target, context, targetlanguage
            self.migrated = []

            self.poedit_dir = path.expanduser('~/.poedit')

            #TODO: check if we can do better than hardcoding the kbabel location
            #this path is specified in ~/.kde/config/kbabel.defaultproject and kbabeldictrc
            self.kbabel_dir = path.expanduser('~/.kde/share/apps/kbabeldict/dbsearchengine')

            self.lokalize_rc = path.expanduser('~/.kde/share/config/lokalizerc')
            self.lokalize_tm_dir = path.expanduser('~/.kde/share/apps/lokalize/')

            self.poedit_settings_import()
            self.poedit_tm_import()
            self.kbabel_tm_import()
            self.lokalize_settings_import()
            self.lokalize_tm_import()

            if self.migrated:
                message = _('Migration was successfully completed') + '\n\n'
                message += _('The following items were migrated:') + '\n\n'
                #l10n: This message indicates the formatting of a bullet point. Most
                #languages wouldn't need to change it.
                message += u"\n".join([u" • %s" % item for item in self.migrated])
                #   (we can mark this ^^^ for translation if somebody asks)
                self.main_controller.show_info(_('Migration completed'), message)
            else:
                message = _("Virtaal was not able to migrate any settings or data")
                self.main_controller.show_info(_('Nothing migrated'), message)
            logging.debug('Migration plugin executed')

        pan_app.settings.plugin_state[self.internal_name] = "disabled"

    def poedit_settings_import(self):
        """Attempt to import the settings from Poedit."""
        config_filename = path.join(self.poedit_dir, 'config')
        get_thing = None
        if not path.exists(config_filename):
            try:
                import _winreg
            except Exception, e:
                return

            def get_thing(section, item):
                key = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER, r"Software\Vaclav Slavik\Poedit\%s" % section)
                data = None
                try:
                    # This is very inefficient, but who cares?
                    for i in range(100):
                        name, data, type = _winreg.EnumValue(key, i)
                        if name == item:
                            break
                except EnvironmentError, e:
                    pass
                except Exception, e:
                    logging.exception("Error obtaining from registry: %s, %s", section, item)
                return data

        else:
            self.poedit_config = ConfigParser.ConfigParser()
            poedit_config_file = open(config_filename, 'r')
            contents = StringIO.StringIO('[poedit_headerless_file]\n' + poedit_config_file.read())
            poedit_config_file.close()
            self.poedit_config.readfp(contents)
            def get_thing(section, item):
                dictionary = dict(self.poedit_config.items(section or 'poedit_headerless_file'))
                return dictionary.get(item, None)

        if get_thing is None:
            return

        pan_app.settings.general['lastdir'] = get_thing('', 'last_file_path')
        pan_app.settings.translator['name'] = get_thing('', 'translator_name')
        pan_app.settings.translator['email'] = get_thing('', 'translator_email')
        pan_app.settings.write()
        self.poedit_database_path = get_thing('TM', 'database_path')
        self.poedit_languages = []
        languages = get_thing('TM', 'languages')
        if languages:
            self.poedit_languages = languages.split(':')

        self.migrated.append(_("Poedit settings"))

    def poedit_tm_import(self):
        """Attempt to import the Translation Memory used in KBabel."""
        if not hasattr(self, "poedit_database_path"):
            return

        # import each language separately
        for lang in self.poedit_languages:
            strings_db_file = path.join(self.poedit_database_path, lang, 'strings.db')
            translations_db_file = path.join(self.poedit_database_path, lang, 'translations.db')
            if not path.exists(strings_db_file) or not path.exists(translations_db_file):
                continue
            sources = bsddb.hashopen(strings_db_file, 'r')
            targets = bsddb.rnopen(translations_db_file, 'r')
            for source, str_index in sources.iteritems():
                unit = {"context" : ""}
                # the index is a four byte integer encoded as a string
                # was little endian on my machine, not sure if it is universal
                index = struct.unpack('i', str_index)
                target = targets[index[0]][:-1] # null-terminated
                unit["source"] = _prepare_db_string(source)
                unit["target"] = _prepare_db_string(target)
                self.tmdb.add_dict(unit, "en", lang, commit=False)
            self.tmdb.connection.commit()

            logging.debug('%d units migrated from Poedit TM: %s.' % (len(sources), lang))
            sources.close()
            targets.close()
            self.migrated.append(_("Poedit's Translation Memory: %(database_language_code)s") % \
                    {"database_language_code": lang})

    def kbabel_tm_import(self):
        """Attempt to import the Translation Memory used in KBabel."""
        if not path.exists(self.kbabel_dir):
            return
        for tm_filename in os.listdir(self.kbabel_dir):
            if not tm_filename.startswith("translations.") or not tm_filename.endswith(".db"):
                continue
            tm_file = path.join(self.kbabel_dir, tm_filename)
            lang = tm_filename.replace("translations.", "").replace(".db", "")
            translations = bsddb.btopen(tm_file, 'r')

            for source, target in translations.iteritems():
                unit = {"context" : ""}
                source = source[:-1] # null-terminated
                target = target[16:-1] # 16 bytes of padding, null-terminated
                unit["source"] = _prepare_db_string(source)
                unit["target"] = _prepare_db_string(target)
                self.tmdb.add_dict(unit, "en", lang, commit=False)
            self.tmdb.connection.commit()

            logging.debug('%d units migrated from KBabel %s TM.' % (len(translations), lang))
            translations.close()
            self.migrated.append(_("KBabel's Translation Memory: %(database_language_code)s") % \
                      {"database_language_code": lang})

    def lokalize_settings_import(self):
        """Attempt to import the settings from Lokalize."""
        if not path.exists(self.lokalize_rc):
            return

        lokalize_config = ConfigParser.ConfigParser()
        lokalize_config.read(self.lokalize_rc)
        lokalize_identity = dict(lokalize_config.items('Identity'))

        pan_app.settings.translator['name'] = lokalize_identity['authorname']
        pan_app.settings.translator['email'] = lokalize_identity['authoremail']
        pan_app.settings.translator['team'] = lokalize_identity['defaultmailinglist']
        pan_app.settings.general['lastdir'] = path.dirname(dict(lokalize_config.items('State'))['project'])

        pan_app.settings.write()
        self.migrated.append(_("Lokalize settings"))

    def lokalize_tm_import(self):
        """Attempt to import the Translation Memory used in Lokalize."""
        if not path.isdir(self.lokalize_tm_dir):
            return
        databases = [name for name in os.listdir(self.lokalize_tm_dir) if path.exists(name)]
        for database in databases:
            self.do_lokalize_tm_import(database)

    def do_lokalize_tm_import(self, filename):
        """Import the given Translation Memory file used by Lokalize."""
        lang = self.main_controller.lang_controller.target_lang.code
        connection = dbapi2.connect(filename)
        cursor = connection.cursor()
        cursor.execute("""SELECT english, target from tm_main;""")
        for (source, target) in cursor:
            unit = { "source" : source,
                     "target" : target,
                     "context" : ""
                     }
            self.tmdb.add_dict(unit, "en", lang, commit=False)
        self.tmdb.connection.commit()
        connection.close()
        self.migrated.append(_("Lokalize's Translation Memory: %(database_name)s") % \
                {"database_name": path.basename(filename)})
