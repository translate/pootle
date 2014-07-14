#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2014 Evernote Corporation
#
# This file is part of Pootle.
#
# Pootle is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your
# option) any later version.
#
# Pootle is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along
# with Pootle; if not, see <http://www.gnu.org/licenses/>.

__all__ = ('UserAdminView', 'UserAPIView')

from django.contrib.auth import get_user_model
from django.views.generic import TemplateView

from pootle.core.views import APIView, SuperuserRequiredMixin
from pootle_app.forms import UserForm


class UserAdminView(SuperuserRequiredMixin, TemplateView):
    template_name = 'admin/users.html'


class UserAPIView(SuperuserRequiredMixin, APIView):
    model = get_user_model()
    base_queryset = get_user_model().objects.order_by('-id')
    add_form_class = UserForm
    edit_form_class = UserForm
    page_size = 10
    search_fields = ('username', 'full_name', 'email')
