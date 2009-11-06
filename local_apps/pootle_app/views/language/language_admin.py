#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Copyright 2008 Zuza Software Foundation
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

from django.shortcuts import get_object_or_404, render_to_response
from django.template import RequestContext
from django.utils.translation import ugettext as _
from django.core.exceptions import PermissionDenied

from pootle_app.models.language import Language
from pootle_app.models.permissions import get_matching_permissions, check_permission
from pootle_app.models.profile import get_profile
from pootle_app.views.language.admin_permissions import process_update as process_permission_update

from pootle.i18n.gettext import tr_lang


def view(request, language_code):
    # Check if the user can access this view
    language = get_object_or_404(Language, code=language_code)
    request.permissions = get_matching_permissions(get_profile(request.user),
                                                   language.directory)
    if not check_permission('administrate', request):
        raise PermissionDenied(_("You do not have administration rights for this language."))

    permission_set_formset = process_permission_update(request, language.directory)

    template_vars = {
        "norights_text":          _("You do not have the rights to administer this Language."),
        "language":               { 'code': language_code,
                                    'name': tr_lang(language.fullname) },
        "permissions_title":      _("User Permissions"),
        "username_title":         _("Username"),
        "permission_set_formset": permission_set_formset,
        "adduser_text":           _("(select to add user)"),
        "hide_fileadmin_links":   True,
        "feed_path":              '%s/' % language.code,
    }
    return render_to_response("language/language_admin.html", template_vars,
                              context_instance=RequestContext(request))
