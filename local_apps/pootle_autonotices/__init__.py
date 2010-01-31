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

from django.db.models.signals      import post_save
from django.contrib.auth.models import User

from pootle_app.models import Language, Project
from pootle_translationproject.models import TranslationProject
import signals

post_save.connect(signals.new_language, sender=Language)
post_save.connect(signals.new_project, sender=Project)
post_save.connect(signals.new_user, sender=User)
post_save.connect(signals.new_translationproject, sender=TranslationProject)

from pootle_app.models.signals import post_vc_update, post_vc_commit
from pootle_app.models.signals import post_template_update, post_file_upload
post_vc_update.connect(signals.updated_from_version_control)
post_vc_commit.connect(signals.committed_to_version_control)
post_template_update.connect(signals.updated_from_template)
post_file_upload.connect(signals.file_uploaded)

from pootle_store.signals import post_unit_update
post_unit_update.connect(signals.unit_updated)
