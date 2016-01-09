#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import os
import re
import urllib
import urlparse

from django.core.urlresolvers import reverse, resolve
from django.utils.functional import cached_property


class PathValidator(object):
    """Converts a request.path into parts for matching pootle_path
    with a regex
    """

    def __init__(self, path):
        self._path = path

    @cached_property
    def kwargs(self):
        if not self.path:
            return {}
        return resolve(self.path).kwargs

    @property
    def directory_path(self):
        if not self.path:
            return ""
        directory = self.kwargs.get("dir_path", "") or ""
        if directory and not directory.endswith("/"):
            directory = "%s/" % directory
        return directory

    @property
    def filename(self):
        return self.kwargs.get("filename", "") or ""

    @property
    def language_code(self):
        return self.kwargs.get("language_code", None) or None

    @cached_property
    def path(self):
        if not self._path:
            return self._path
        path = self._extracted_vfolder_and_path[1]
        parts = path.split("/")
        if "." in parts[-1]:
            return "/%s" % path.strip("/")
        return "/%s/" % path.strip("/")

    @property
    def project_code(self):
        return self.kwargs.get("project_code", None) or None

    @property
    def regex(self):
        if not (self.project_code or self.language_code):
            return None
        regex = r"^/"

        if self.language_code:
            regex = r"%s%s/" % (regex, self.language_code)
        else:
            regex = r"%s[a-zA-Z0-9\-\_]*/" % regex

        if self.project_code:
            regex = r"%s%s/" % (regex, self.project_code)
        else:
            regex = r"%s[a-zA-Z0-9\-\_]*/" % regex

        if self.directory_path:
            regex = r"%s%s" % (regex, self.directory_path)

        if self.filename:
            regex = (
                r"%s%s$"
                % (regex,
                   self.filename.replace(".", "\.")))
        return regex

    @cached_property
    def vfolder(self):
        return self._extracted_vfolder_and_path[0]

    @cached_property
    def _extracted_vfolder_and_path(self):
        from virtualfolder.helpers import extract_vfolder_from_path
        # extract_vfolder_path_old)
        from virtualfolder.utils import vfolders_installed

        if not vfolders_installed():
            return None, self._path
        res1 = extract_vfolder_from_path(self._path)
        # res2 = extract_vfolder_path_old(self._path)
        return res1


def split_pootle_path(pootle_path):
    import os

    slash_count = pootle_path.count(u'/')
    parts = pootle_path.split(u'/', 3)[1:]

    language_code = None
    project_code = None
    ctx = ''

    if slash_count != 0 and pootle_path != '/projects/':
        if slash_count == 2:
            language_code = parts[0]
        elif pootle_path.startswith('/projects/'):
            project_code = parts[1]
            ctx = parts[2]
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
    res = [pootle_path]

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
                      sort=None, search=None, sfields=None,
                      check_category=None):
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
    elif check_category is not None:
        filter_string = '#filter=checks&category=%s' % check_category
    elif search is not None:
        filter_string = '#search=%s' % urllib.quote_plus(search)
        if sfields is not None:
            if not isinstance(sfields, list):
                sfields = [sfields]
            filter_string += '&sfields=%s' % ','.join(sfields)

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
        referer_query = parsed_referer.query
        server_host = request.get_host()

        if referer_host == server_host and '/translate/' not in referer_path:
            # Remove query string if present
            if referer_query:
                referer_url = referer_url[:referer_url.index('?')]

            # But ensure `?details` is not missed out
            if 'details' in referer_query:
                referer_url = '%s?details' % referer_url

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
