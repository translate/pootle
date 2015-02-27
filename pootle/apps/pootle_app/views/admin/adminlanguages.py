#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL2
# license. See the LICENSE file for a copy of the license and the AUTHORS file
# for copyright and authorship information.

from django.core.urlresolvers import reverse

from pootle.core.decorators import admin_required
from pootle_app.forms import MyLanguageAdminForm
from pootle_app.views.admin import util
from pootle_language.models import Language


@admin_required
def view(request):

    def generate_link(language):
        perms_url = reverse('pootle-language-admin-permissions',
                            args=[language.code])
        return '<a href="%s">%s</a>' % (perms_url, language.code)

    return util.edit(request, 'admin/languages.html', Language,
                     link=generate_link, form=MyLanguageAdminForm,
                     can_delete=True)
