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
    langcodes = [language.code for language in Language.objects.iterator()]
    content = "User-agent: *\n"
    for path in ["accounts", "projects", "unit", "xhr"]:
        content += "Disallow: /%s/\n" % path
    for langcode in langcodes:
        content += "Disallow: /%s/\n" % langcode
    return HttpResponse(content, content_type="text/plain")
