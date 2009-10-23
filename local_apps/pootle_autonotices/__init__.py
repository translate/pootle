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

from django.db.models.signals      import pre_delete, post_init, pre_save, post_save
from django.contrib.auth.models import User

from pootle_app.models import Language, Project, TranslationProject

import signals

post_save.connect(signals.new_language, sender=Language)
post_save.connect(signals.new_project, sender=Project)
post_save.connect(signals.new_user, sender=User)
post_save.connect(signals.new_translationproject, sender=TranslationProject)
