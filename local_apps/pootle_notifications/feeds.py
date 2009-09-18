#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009 Zuza Software Foundation
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

from django.contrib.syndication.feeds import Feed, FeedDoesNotExist
from pootle_notifications.models import Notices
from pootle_app.models import Language, TranslationProject
from pootle.i18n.gettext import tr_lang
from django.contrib.syndication import feeds
from django.http import HttpResponse, Http404,  HttpResponseForbidden
from django.utils.translation import ugettext as _

from pootle_app.models.permissions import get_matching_permissions
from pootle_app.models.profile import get_profile

def NoticeFeeds(request, url):
    param = ''
    denied = False
    try:
        default_param = url.split('/')
        if len(default_param) == 1 :
            f = LanguageFeeds
            param = default_param[0]
            lang = Language.objects.get(code=param)
            if 'view' not in get_matching_permissions(get_profile(request.user), lang.directory):
                denied = True

        elif len(default_param) == 2 :
            f = TransProjectFeeds
            param = default_param[1] + "/" + default_param[0]
            transproj = TranslationProject.objects.get(real_path = param)
            if 'view' not in get_matching_permissions(get_profile(request.user), transproj.directory):
                denied = True

        else:
            f = ''
            denied = True
    except ValueError:
        slug, param = url, ''

    if denied:
        return HttpResponseForbidden()
    try:
        feedgen = f(None, request).get_feed(param)
    except feeds.FeedDoesNotExist:
        raise Http404, "Invalid feed parameters."

    response = HttpResponse(mimetype=feedgen.mime_type)
    feedgen.write(response, 'utf-8')
    return response

class LanguageFeeds(Feed):
    link = "/feeds/"
    description = _("Feeds for language notices")
    #title = "Language Feeds"

    def get_object(self, bits):
        """Get object_id and content_type_id based on bits."""
        lang = Language.objects.get(code=bits[0])
        content = Notices(content_object = lang)
        return content

    def title(self, obj):
        lang = Language.objects.get(id = obj.object_id)
        return _('News for %(language)s', {"language": tr_lang(self.request, lang.fullname)})

    def items(self, obj):
        return Notices.objects.get_notices(obj)


class TransProjectFeeds(Feed):
    link = "/feeds/"
    description = _("Feeds for translation project notices")
    title = _("Translation project Feeds")

    def get_object(self, bits):
        """Get object_id and content_type_id based on bits."""
        real_path = bits[0] + "/" + bits[1]
        trans_proj = TranslationProject.objects.get(real_path=real_path)
        content = Notices(content_object = trans_proj)
        return content

    def title(self, obj):
        trans_proj = TranslationProject.objects.get(id = obj.object_id)
        return _('News about the translation of %(project)s into %(language)s',
                {"language": tr_lang(self.request, trans_proj.language.fullname), "project": tr_lang(self.request, trans_proj.project.fullname)})

    def items(self, obj):
        return Notices.objects.get_notices(obj)
