# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

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
    must_show_announcement = False
    announcements = []

    if SIDEBAR_COOKIE_NAME in request.COOKIES:
        try:
            is_sidebar_open = bool(int(request.COOKIES[SIDEBAR_COOKIE_NAME]))
        except ValueError:
            is_sidebar_open = True

        request.session['is_sidebar_open'] = is_sidebar_open
    else:
        is_sidebar_open = request.session.get('is_sidebar_open', True)

    for item in objects:
        announcement = item.get_announcement(request.user)

        if announcement is None:
            continue

        announcements.append(announcement)

        if request.user.is_anonymous:
            # Do not store announcement mtimes for anonymous user.
            continue

        ann_mtime = dateformat.format(announcement.modified_on, 'U')
        stored_mtime = request.session.get(announcement.virtual_path, None)

        if ann_mtime != stored_mtime:
            # Some announcement has been changed or was never displayed before,
            # so display sidebar and save the changed mtimes in the session to
            # not display it next time unless it is necessary.
            must_show_announcement = True
            request.session[announcement.virtual_path] = ann_mtime

    ctx = {
        'announcements': announcements,
        'is_sidebar_open': must_show_announcement or is_sidebar_open,
        'has_sidebar': len(announcements) > 0,
    }

    return ctx
