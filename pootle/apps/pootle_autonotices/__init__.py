#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009, 2013 Zuza Software Foundation
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

from django.contrib.auth.models import User
from django.db.models.signals import post_save, pre_save

from pootle_app.models.signals import (post_file_upload, post_template_update,
                                       post_vc_commit, post_vc_update)
from pootle_language.models import Language
from pootle_project.models import Project
from pootle_store.models import Unit
from pootle_translationproject.models import TranslationProject

from pootle_autonotices import signals


post_save.connect(signals.new_language, sender=Language)
post_save.connect(signals.new_project, sender=Project)
post_save.connect(signals.new_user, sender=User)
post_save.connect(signals.new_translationproject, sender=TranslationProject)

pre_save.connect(signals.unit_updated, sender=Unit)

post_file_upload.connect(signals.file_uploaded)

post_template_update.connect(signals.updated_against_template)

post_vc_commit.connect(signals.committed_to_version_control)

post_vc_update.connect(signals.updated_from_version_control)
