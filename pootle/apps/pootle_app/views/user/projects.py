# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.


from pootle.core.views.decorators import set_permissions, 
                                        requires_permission_class,
                                        check_user_permission
from pootle_app.views.admin import ProjectGenericAdminView


__all__ = ('ProjectUserView',)


class ProjectUserView(ProjectGenericAdminView):
    template_name = 'projects/admin/user.html'
    page_code = 'user-projects'


    @set_permissions
    @requires_permission_class("add_project")
    def dispatch(self, request, *args, **kwargs):
        return super(ProjectUserView, self).dispatch(request, *args, **kwargs)
