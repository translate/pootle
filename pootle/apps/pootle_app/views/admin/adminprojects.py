#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008-2014 Zuza Software Foundation
# Copyright 2013 Evernote Corporation
#
# This file is part of Pootle.
#
# Pootle is free software; you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# Pootle is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# Pootle; if not, see <http://www.gnu.org/licenses/>.

from django.core.urlresolvers import reverse

from pootle.core.decorators import admin_required
from pootle_app.forms import project_admin_form_factory
from pootle_app.views.admin import util
from pootle_project.models import Project


@admin_required
def view(request):

    def generate_link(project):
        url = reverse('pootle-project-admin-languages', args=[project.code])
        return '<a href="%s">%s</a>' % (url, project.code)

    return util.edit(
            request,
            'admin/projects.html',
            Project,
            link=generate_link,
            form=project_admin_form_factory(),
            exclude=('description', 'report_email'),
            can_delete=True,
    )
