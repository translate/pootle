#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009 Zuza Software Foundation
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

from django.db import models
from django.utils.translation import ugettext_lazy as _

from pootle_app.lib.util import RelatedManager

class Suggestion(models.Model):
    class Meta:
        app_label = "pootle_app"

    objects = RelatedManager()

    state_choices = [('pending', _('Pending')),
                     ('accepted', _('Accepted')),
                     ('rejected', _('Rejected')),
                     ]

    creation_time       = models.DateTimeField(auto_now_add=True, db_index=True)
    translation_project = models.ForeignKey('pootle_translationproject.TranslationProject', db_index=True)
    suggester           = models.ForeignKey('pootle_profile.PootleProfile', null=True, related_name='suggester', db_index=True)
    reviewer            = models.ForeignKey('pootle_profile.PootleProfile', null=True, related_name='reviewer', db_index=True)
    review_time         = models.DateTimeField(null=True, db_index=True)
    unit                = models.IntegerField(null=False, db_index=True)
    state               = models.CharField(max_length=16, default='pending', null=False, choices=state_choices, db_index=True)



