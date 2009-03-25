#!/usr/bin/python
# -*- coding: utf-8 -*-
#  Copyright 2004-2009 Zuza Software Foundation
#
# This file is part of Pootle.
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, see <http://www.gnu.org/licenses/>.

from Pootle import pagelayout
from email.Header import Header
from django.contrib.auth.models import User
from pootle_app.models.profile import get_profile
from Pootle import pan_app








def with_user(username, f):
    try:
        user = User.objects.include_hidden().get(username=username)
        f(user)
        return user
    except User.DoesNotExist:
        return None

 
