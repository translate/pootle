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

from profile import PootleProfile
from store import Store, Unit
from directory import Directory

class Goal(models.Model):
    """A goal is a named collection of files. Goals partition the files of
    translation project. In other words, every file is either in no
    goals or exactly in one goal.
    """
    
    class Meta:
        unique_together = ('name', 'directory')
        app_label = "pootle_app"

    name                = models.CharField(max_length=255, null=False, verbose_name=_("Name"))
    directory           = models.ForeignKey(Directory)
    # A pointer to the TranslationProject of which this Goal is a part.
    # involved with a number of goals.
    profiles            = models.ManyToManyField(PootleProfile, related_name='goals')
    # A store can be part of many goals and a goal can contain many files
    stores              = models.ManyToManyField(Store, related_name='goals')

class Assignment(models.Model):
    class Meta:
        unique_together = ('goal', 'profile')
        app_label = "pootle_app"

    goal    = models.ForeignKey(Goal, db_index=True)
    profile = models.ForeignKey(PootleProfile, db_index=True)

class StoreAssignment(models.Model):
    class Meta:
        app_label = "pootle_app"

    assignment = models.ForeignKey(Assignment)
    store      = models.OneToOneField(Store, db_index=True)
    units      = models.ManyToManyField(Unit, related_name='stores')

