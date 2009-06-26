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

import os

from django.db.models.signals import pre_save
from django.utils.translation import ugettext_lazy as _
from django.db                import models

from translate.filters import checks

from pootle_store.util import relative_real_path, absolute_real_path, statssum

class Project(models.Model):
    class Meta:
        app_label = "pootle_app"
        ordering = ['code']

    code_help_text = u'A short code for the project. This should only contain ASCII characters, numbers, and the underscore (_) character.'
    description_help_text = u'A description of this project. This is useful to give more information or instructions. This field should be valid HTML.'

    checker_choices = [('standard', 'standard')]
    checkers = list(checks.projectcheckers.keys())
    checkers.sort()
    checker_choices.extend([(checker, checker) for checker in checkers])
    local_choices = (
            ('po', 'Gettext PO'),
            ('xlf', 'XLIFF')
    )
    treestyle_choices = (
            # TODO: check that the None is stored and handled correctly
            ('auto', _(u'Automatic detection (slower)')),
            ('gnu', _(u'GNU style: all languages in one directory; files named by language code')),
            ('nongnu', _(u'Non-GNU: Each language in its own directory')),
    )

    code           = models.CharField(max_length=255, null=False, unique=True, db_index=True, help_text=code_help_text)
    fullname       = models.CharField(max_length=255, null=False, verbose_name=_("Full name"))
    description    = models.TextField(blank=True, help_text=description_help_text)
    checkstyle     = models.CharField(max_length=50, default='standard', null=False, choices=checker_choices)
    localfiletype  = models.CharField(max_length=50, default="po", choices=local_choices)
    treestyle      = models.CharField(max_length=20, default='auto', choices=treestyle_choices)
    ignoredfiles   = models.CharField(max_length=255, blank=True, null=False, default="")
    createmofiles  = models.BooleanField(default=False)

    def __unicode__(self):
        return self.fullname

    def getquickstats(self):
        return statssum(self.translationproject_set.all())
        
def create_project_directory(sender, instance, **kwargs):
    project_path = absolute_real_path(instance.code)
    if not os.path.exists(project_path):
        os.mkdir(project_path)

pre_save.connect(create_project_directory, sender=Project)
