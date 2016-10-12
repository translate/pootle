# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import json
from urllib import quote, unquote

from django.utils import dateformat


SIDEBAR_COOKIE_NAME = 'pootle-browser-sidebar'


def get_sidebar_announcements_context(request, objects):
    """Return the announcements context for the browser pages sidebar.

    :param request: a :cls:`django.http.HttpRequest` object.
    :param objects: a tuple of Project, Language and TranslationProject to
                    retrieve the announcements for. Any of those can be
                    missing, but it is recommended for them to be in that exact
                    order.
    """
    announcements = []
    new_cookie_data = {}
    cookie_data = {}

    if SIDEBAR_COOKIE_NAME in request.COOKIES:
        json_str = unquote(request.COOKIES[SIDEBAR_COOKIE_NAME])
        cookie_data = json.loads(json_str)

    is_sidebar_open = cookie_data.get('isOpen', True)

    for item in objects:
        announcement = item.get_announcement(request.user)

        if announcement is None:
            continue

        announcements.append(announcement)
        # The virtual_path cannot be used as is for JSON.
        ann_key = announcement.virtual_path.replace('/', '_')
        ann_mtime = dateformat.format(announcement.modified_on, 'U')
        stored_mtime = cookie_data.get(ann_key, None)

        if ann_mtime != stored_mtime:
            new_cookie_data[ann_key] = ann_mtime

    if new_cookie_data:
        # Some announcement has been changed or was never displayed before, so
        # display sidebar and save the changed mtimes in the cookie to not
        # display it next time unless it is necessary.
        is_sidebar_open = True
        cookie_data.update(new_cookie_data)
        new_cookie_data = quote(json.dumps(cookie_data))

    ctx = {
        'announcements': announcements,
        'is_sidebar_open': is_sidebar_open,
        'has_sidebar': len(announcements) > 0,
    }

    return ctx, new_cookie_data
