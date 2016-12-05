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


SIDEBAR_COOKIE_NAME = 'pootle-browser-open-sidebar'


def get_sidebar_announcements_context(request, objects):
    """Return the announcements context for the browser pages sidebar.

    :param request: a :cls:`django.http.HttpRequest` object.
    :param objects: a tuple of Project, Language and TranslationProject to
                    retrieve the announcements for. Any of those can be
                    missing, but it is recommended for them to be in that exact
                    order.
    """
    must_show_announcement = False
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

        ann_mtime = dateformat.format(announcement.modified_on, 'U')
        stored_mtime = request.session.get(announcement.virtual_path, None)

        if ann_mtime != stored_mtime:
            # Some announcement has been changed or was never displayed before,
            # so display sidebar and save the changed mtimes in the session to
            # not display it next time unless it is necessary.
            must_show_announcement = True
            request.session[announcement.virtual_path] = ann_mtime

    if must_show_announcement and not is_sidebar_open:
        is_sidebar_open = True
        cookie_data['isOpen'] = is_sidebar_open
        new_cookie_data = quote(json.dumps(cookie_data))

    ctx = {
        'announcements': announcements,
        'is_sidebar_open': is_sidebar_open,
        'has_sidebar': len(announcements) > 0,
    }

    return ctx, new_cookie_data
