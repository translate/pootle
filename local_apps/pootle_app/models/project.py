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
from translate.lang.data import langcode_re

from pootle_store.util import absolute_real_path, statssum
from pootle_misc.util import getfromcache
from pootle_misc.baseurl import l

class Project(models.Model):
    class Meta:
        app_label = "pootle_app"
        ordering = ['code']

    code_help_text = _('A short code for the project. This should only contain ASCII characters, numbers, and the underscore (_) character.')
    description_help_text = _('A description of this project. This is useful to give more information or instructions. This field should be valid HTML.')

    checker_choices = [('standard', 'standard')]
    checkers = list(checks.projectcheckers.keys())
    checkers.sort()
    checker_choices.extend([(checker, checker) for checker in checkers])
    local_choices = (
            ('po', _('Gettext PO')),
            ('xlf', _('XLIFF'))
    )
    treestyle_choices = (
            # TODO: check that the None is stored and handled correctly
            ('auto', _('Automatic detection (slower)')),
            ('gnu', _('GNU style: all languages in one directory; files named by language code')),
            ('nongnu', _('Non-GNU: Each language in its own directory')),
    )

    code           = models.CharField(max_length=255, null=False, unique=True, db_index=True, verbose_name=_('Code'), help_text=code_help_text)
    fullname       = models.CharField(max_length=255, null=False, verbose_name=_("Full Name"))
    description    = models.TextField(blank=True, help_text=description_help_text)
    checkstyle     = models.CharField(max_length=50, default='standard', null=False, choices=checker_choices, verbose_name=_('Quality Checks'))
    localfiletype  = models.CharField(max_length=50, default="po", choices=local_choices, verbose_name=_('File Type'))
    treestyle      = models.CharField(max_length=20, default='auto', choices=treestyle_choices, verbose_name=_('Project Tree Style'))
    ignoredfiles   = models.CharField(max_length=255, blank=True, null=False, default="", verbose_name=_('Ignore Files'))

    def __unicode__(self):
        return self.fullname

    @getfromcache
    def getquickstats(self):
        return statssum(self.translationproject_set.all())

    def translated_percentage(self):
        return int(100.0 * self.getquickstats()['translatedsourcewords'] / max(self.getquickstats()['totalsourcewords'], 1))

    def _get_pootle_path(self):
        return "/projects/" + self.code + "/"
    pootle_path = property(_get_pootle_path)

    def get_real_path(self):
        return absolute_real_path(self.code)

    def get_absolute_url(self):
        return l(self.pootle_path)

    def get_template_filtetype(self):
        if self.localfiletype == 'po':
            return 'pot'
        else:
            return self.localfiletype
        
    def file_belongs_to_project(self, filename, match_templates=True):
        """tests if filename matches project filetype (ie. extension),
        if match_templates is true will also check if file matches
        template filetype"""
        
        return filename.endswith(os.path.extsep + self.localfiletype) or \
               match_templates and filename.endswith(os.path.extsep + self.get_template_filtetype())
    
    def get_treestyle(self):
        """returns the real treestyle, if treestyle is set to auto it
        checks the project directory and tries to guess if it is gnu
        style or nongnu style.

        we are biased towards nongnu because it makes managing project
        from the web easier"""
        
        if self.treestyle != "auto":
            return self.treestyle
        else:
            dirlisting = os.walk(self.get_real_path())
            dirpath, dirnames, filenames = dirlisting.next()
            
            if not dirnames:
                # no subdirectories                        
                if filter(self.file_belongs_to_project, filenames):
                    # translation files found, assume gnu
                    return "gnu"
                else:
                    # no subdirs and no translation files, assume nongnu
                    return "nongnu"
            else:
                # there are subdirectories
                if filter(lambda dirname: dirname == 'templates' or langcode_re.match(dirname), dirnames):
                    # found language dirs assume nongnu
                    return "nongnu"
                else:
                    # no language subdirs found, look for any translation file
                    for dirpath, dirnames, filenames in os.walk(self.get_real_path()):
                        if filter(self.file_belongs_to_project, filenames):
                            return "gnu"
            # when unsure assume nongnu
            return "nongnu"

    
def create_project_directory(sender, instance, **kwargs):
    project_path = absolute_real_path(instance.code)
    if not os.path.exists(project_path):
        os.makedirs(project_path)
    
pre_save.connect(create_project_directory, sender=Project)
