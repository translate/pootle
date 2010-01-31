#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008 Zuza Software Foundation
#
# This file is part of translate.
#
# translate is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# translate is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with translate; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

from django.utils.translation import ugettext as _
from pootle_app.views.admin import util
from pootle_language.models import Language
from pootle_app.admin import MyLanguageAdminForm

@util.user_is_admin
def view(request):
    model_args = {}
    model_args['title'] = _("Languages")
    model_args['submitname'] = "changelanguages"
    model_args['formid'] = "languages"
    link = '/%s/admin.html'
    return util.edit(request, 'admin/admin_general_languages.html', Language, model_args, link,
                     form=MyLanguageAdminForm, can_delete=True)
    
              
