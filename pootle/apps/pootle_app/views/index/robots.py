# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.http import HttpResponse

from pootle_language.models import Language


def view(request):
    """generates the robots.txt file"""
    content = "User-agent: *\n"
    content += "Allow: /\n"
    for path in ["projects", "projects/*", "pages"]:
        content += "Allow: /%s/\n" % path
    for path in ["*/translate", "*/*/translate",
                 "*/export-view", "*/*/export-view",
                 "user/*/stats",
                 "accounts", "unit", "xhr"]:
        content += "Disallow: /%s/\n" % path
    return HttpResponse(content, content_type="text/plain")
