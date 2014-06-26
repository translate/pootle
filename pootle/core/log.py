#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2013 Evernote Corporation
#
# This file is part of Pootle.
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

import logging


# Log actions
TRANSLATION_ADDED = 'A'
TRANSLATION_CHANGED = 'C'
TRANSLATION_DELETED = 'D'
UNIT_ADDED = 'UA'
UNIT_DELETED = 'UD'
UNIT_OBSOLETE = 'UO'
STORE_ADDED = 'SA'
STORE_DELETED = 'SD'
CMD_EXECUTED = 'X'
MUTE_QUALITYCHECK = "QM"
UNMUTE_QUALITYCHECK = "QU"


def log(message):
    logger = logging.getLogger('action')
    logger.info(message)


def action_log(*args, **kwargs):
    logger = logging.getLogger('action')
    d = {}
    for p in ['user', 'lang', 'action', 'unit', 'path']:
        d[p] = kwargs.pop(p, '')

    tr = kwargs.pop('translation', '')
    tr = tr.replace("\\", "\\\\")
    tr = tr.replace("\n", "\\\n")
    d['translation'] = tr

    message = "%(user)s\t%(action)s\t%(lang)s\t%(unit)s\t%(path)s\t%(translation)s" % d

    logger.info(message)


def cmd_log(*args, **kwargs):
    import os
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pootle.settings")
    from datetime import datetime
    from django.conf import settings
    from pootle_app.project_tree import ensure_target_dir_exists

    _log = settings.LOGGING
    filename = _log.get("handlers", {}).get("log_action", {}).get("filename")
    if not filename:
        return
    ensure_target_dir_exists(filename)

    logfile = open(filename, "a")
    datefmt = _log.get("formatters", {}).get("action", {}).get("datefmt", "%Y-%m-%dT%H:%M:%S")

    message = "%(user)s\t%(action)s\t%(cmd)s" % {
        'user': 'system',
        'action': CMD_EXECUTED,
        'cmd': " ".join(args)
    }
    d = {
         'message': message,
         'datefmt': datetime.now().strftime(datefmt)
    }
    logfile.write("[%(datefmt)s]\t%(message)s\n" % d)
    logfile.close()


def store_log(*args, **kwargs):
    logger = logging.getLogger('action')
    d = {}
    for p in ['user', 'path', 'action', 'store']:
        d[p] = kwargs.pop(p, '')

    message = "%(user)s\t%(action)s\t%(path)s\t%(store)s" % d

    logger.info(message)
