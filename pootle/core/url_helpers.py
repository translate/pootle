#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2013 Zuza Software Foundation
# Copyright 2013-2014 Evernote Corporation
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

import os
import re
import urlparse

from django.core.urlresolvers import reverse


def split_pootle_path(pootle_path):
    """Split an internal `pootle_path` into proper parts.

    :return: A tuple containing each part of a pootle_path`::
        (language code, project code, directory path, filename)
    """
    slash_count = pootle_path.count(u'/')
    parts = pootle_path.split(u'/', 3)[1:]

    language_code = None
    project_code = None
    ctx = ''

    if slash_count != 0 and pootle_path != '/projects/':
        # /<lang_code>/
        if slash_count == 2:
            language_code = parts[0]
        # /projects/<project_code>/
        elif pootle_path.startswith('/projects/'):
            project_code = parts[1]
            ctx = parts[2]
        # /<lang_code>/<project_code>/*
        elif slash_count != 1:
            language_code = parts[0]
            project_code = parts[1]
            ctx = parts[2]

    dir_path, filename = os.path.split(ctx)
    if dir_path:
        dir_path = u'/'.join([dir_path, ''])  # Add trailing slash

    return (language_code, project_code, dir_path, filename)


def to_tp_relative_path(pootle_path):
    """Returns a path relative to translation projects.

    If `pootle_path` is `/af/project/dir1/dir2/file.po`, this will
    return `dir1/dir2/file.po`.
    """
    return u'/'.join(pootle_path.split(u'/')[3:])


def get_all_pootle_paths(pootle_path):
    """Get list of `pootle_path` for all parents."""
    res = []
    res.append(pootle_path)
    if pootle_path == '' or pootle_path[-1] != u'/':
        pootle_path += u'/'
    while True:
        chunks = pootle_path.rsplit(u'/', 2)
        slash_count = chunks[0].count(u'/')
        pootle_path = chunks[0] + u'/'
        if slash_count > 1:
            res.append(pootle_path)
        else:
            if slash_count == 1 and pootle_path != u'/projects/':
                # omit chunk[0] which is a language_code
                # since language is inherited from a (non cached) TreeItem
                # chunk[1] is a project_code
                res.append(u'/projects/%s/' % chunks[1])
            break

    return res


def get_path_sortkey(path):
    """Returns the sortkey to use for a `path`."""
    if path == '' or path.endswith('/'):
        return path

    (head, tail) = os.path.split(path)
    return u'~'.join([head, path])


def get_path_parts(path):
    """Returns a list of `path`'s parent paths plus `path`."""
    if not path:
        return []

    (parent, filename) = os.path.split(path)
    parent_parts = parent.split(u'/')

    if len(parent_parts) == 1 and parent_parts[0] == u'':
        parts = []
    else:
        parts = [u'/'.join(parent_parts[:parent_parts.index(part) + 1] + [''])
                 for part in parent_parts]

    # If present, don't forget to include the filename
    if path not in parts:
        parts.append(path)

    # Everything has a root
    parts.insert(0, u'')

    return parts


def get_editor_filter(state=None, check=None, user=None, month=None,
                      sort=None):
    """Return a filter string to be appended to a translation URL."""
    filter_string = ''

    if state is not None:
        filter_string = '#filter=%s' % state
        if user is not None:
            filter_string += '&user=%s' % user
        if month is not None:
            filter_string += '&month=%s' % month

    elif check is not None:
        filter_string = '#filter=checks&checks=%s' % check

    if sort is not None:
        if filter_string:
            filter_string += '&sort=%s' % sort
        else:
            filter_string = '#sort=%s' % sort

    return filter_string


def get_previous_url(request):
    """Returns the current domain's referer URL.

    It also discards any URLs that might come from translation editor
    pages, assuming that any URL path containing `/translate/` refers to
    an editor instance.

    If none of the conditions are met, the URL of the app's home is
    returned.

    :param request: Django's request object.
    """
    referer_url = request.META.get('HTTP_REFERER', '')

    if referer_url:
        parsed_referer = urlparse.urlparse(referer_url)
        referer_host = parsed_referer.netloc
        referer_path = parsed_referer.path
        server_host = request.get_host()

        if referer_host == server_host and '/translate/' not in referer_path:
            # Remove query string if present
            if '?' in referer_url:
                referer_url = referer_url[:referer_url.index('?')]

            return referer_url

    return reverse('pootle-home')


def urljoin(base, *url_parts):
    """Joins URL parts with a `base` and removes any duplicated slashes in
    `url_parts`.
    """
    new_url = urlparse.urljoin(base, '/'.join(url_parts))
    new_url = list(urlparse.urlparse(new_url))
    new_url[2] = re.sub('/{2,}', '/', new_url[2])

    return urlparse.urlunparse(new_url)
