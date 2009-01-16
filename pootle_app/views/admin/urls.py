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

from django.conf.urls.defaults import *
import view

urlpatterns = patterns('',
    (r'users.html$',     view.edit, {'template': 'adminusers.html',     'model_class': view.User, 
                                     'fields': ('username', 'first_name', 'last_name', 'email', 'is_active'),
                                     'can_delete': True}),
    (r'languages.html$', view.edit, {'template': 'adminlanguages.html', 'model_class': view.Language, 'can_delete': True }),
    (r'projects.html$',  view.edit, {'template': 'adminprojects.html',  'model_class': view.Project,  
                                     'exclude': ('description'),
                                     'can_delete': True  }),
    (r'(/|index.html)?$',  view.index),
)
