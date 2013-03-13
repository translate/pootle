#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009-2012 Zuza Software Foundation
#
# This file is part of Pootle.
#
# Pootle is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# Pootle is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Pootle; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

from pootle_misc.baseurl import l


def translate(path_obj, state=None, check=None, user=None):
    # In Pootle, URLs ending in translate.html are used when the user
    # translates all files in a directory (for example, if the user is
    # going through all fuzzy translations in a directory).
    path = path_obj.pootle_path
    if path.endswith('/'):
        path += 'translate.html'
    else:
        path += '/translate/'

    if state:
        path += '#filter=%s' % state
        if user:
            path += '&user=%s' % user
    elif check:
        path += '#filter=checks,%s' % check

    return l(path)


def download_zip(path_obj):
    if path_obj.is_dir:
        current_folder = path_obj.pootle_path
    else:
        current_folder = path_obj.parent.pootle_path
    # FIXME: ugly URL, django.core.urlresolvers.reverse() should work
    archive_name = "%sexport/zip" % current_folder
    return l(archive_name)


def export(pootle_path, format):
    return l('/export-file/%s%s' % (format, pootle_path))


def commit(path_obj):
    return  l(path_obj.pootle_path + '/commit')


def update(path_obj):
    return  l(path_obj.pootle_path + '/update')


def commit_all(path_obj):
    return  l(path_obj.pootle_path + 'commit_all')


def update_all(path_obj):
    return  l(path_obj.pootle_path + 'update_all')
