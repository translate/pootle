#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008-2010,2012 Zuza Software Foundation
# Copyright 2013 Evernote Corporation
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

from pootle.core.decorators import admin_required
from pootle_app.views.admin import util
from pootle_language.models import Language
from pootle_app.admin import MyLanguageAdminForm

@admin_required
def view(request):
    return util.edit(request, 'admin/admin_general_languages.html', Language,
                     link='/%s/admin.html', form=MyLanguageAdminForm,
                     exclude='description', can_delete=True)
