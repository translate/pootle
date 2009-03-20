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

from django.db import models
from django.utils.translation import ugettext_lazy as _

from pootle_app.models.fs_models import Store

class UnitManager(models.Manager):
    def get_or_make(self, store, index, source, target):
        try:
            return self.get(store=store, index=index, source=source, target=target)
        except self.model.DoesNotExist:
            unit = Unit(store=store, index=index, source=source, target=target)
            unit.save()
            return unit

class Unit(models.Model):
    class Meta:
        app_label = "pootle_app"

    objects = UnitManager()

    store   = models.ForeignKey(Store, related_name='units', db_index=True)
    index   = models.IntegerField(db_index=True)
    source  = models.TextField()
    target  = models.TextField()
    state   = models.CharField(max_length=255, db_index=True)
