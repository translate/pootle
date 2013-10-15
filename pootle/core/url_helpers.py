#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2013 Zuza Software Foundation
#
# This file is part of Pootle.
#
# Pootle is free software; you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# Pootle is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# Pootle; if not, see <http://www.gnu.org/licenses/>.

import os


def split_pootle_path(pootle_path):
    """Split an internal `pootle_path` into proper parts.

    :return: A tuple containing each part of a pootle_path`::
        (language code, project code, directory path, filename)
    """
    slash_count = pootle_path.count('/')
    parts = pootle_path.split(u'/', 3)[1:]

    language_code = None
    project_code = None
    ctx = ''

    if slash_count != 0:
        # /<lang_code>/
        if slash_count == 2:
            language_code = parts[0]
        # /projects/<project_code>/
        elif slash_count == 3 and pootle_path.startswith('/projects/'):
            project_code = parts[1]
        # /<lang_code>/<project_code>/*
        elif slash_count != 1:
            language_code = parts[0]
            project_code = parts[1]
            ctx = parts[2]

    dir_path, filename = os.path.split(ctx)
    if dir_path:
        dir_path = u'/'.join([dir_path, ''])  # Add trailing slash

    return (language_code, project_code, dir_path, filename)


def get_editor_filter(state=None, check=None, user=None, goal=None):
    """Return a filter string to be appended to a translation URL."""
    filter_string = ''

    if state is not None:
        filter_string = '#filter=%s' % state
        if user is not None:
            filter_string += '&user=%s' % user
    elif check is not None:
        filter_string = '#filter=checks&checks=%s' % check

    if goal is not None:
        if not filter_string:
            filter_string = '#goal=%s' % goal
        else:
            filter_string += '&goal=%s' % goal

    return filter_string
