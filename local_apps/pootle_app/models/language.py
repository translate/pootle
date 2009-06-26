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

from django.utils.translation import ugettext_lazy as _
from django.db                import models
from pootle_app.models.directory        import Directory
from django.db.models.signals           import pre_save

class Language(models.Model):
    class Meta:
        app_label = "pootle_app"
        ordering = ['code']

    code_help_text = u'ISO 639 language code for the language, possibly followed by an underscore (_) and an ISO 3166 country code. <a href="http://www.w3.org/International/articles/language-tags/">More information</a>'
    nplurals_help_text = u'For more information, visit <a href="http://translate.sourceforge.net/wiki/l10n/pluralforms">our wiki page</a> on plural forms'
    pluralequation_help_text = u'For more information, visit <a href="http://translate.sourceforge.net/wiki/l10n/pluralforms">our wiki page</a> on plural forms'
    specialchars_help_text = u'Enter any special characters that users might find difficult to type'

    nplural_choices = ((0, u'unknown'), (1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6))

    code           = models.CharField(max_length=50, null=False, unique=True, db_index=True, help_text=code_help_text)
    fullname       = models.CharField(max_length=255, null=False, verbose_name=_("Full Name"))
    specialchars   = models.CharField(max_length=255, blank=True, verbose_name=_("Special Chars"), help_text=specialchars_help_text)
    nplurals       = models.SmallIntegerField(default=0, choices=nplural_choices, verbose_name=_("Number of Plurals"), help_text=nplurals_help_text)
    pluralequation = models.CharField(max_length=255, blank=True, verbose_name=_("Plural Equation"), help_text=pluralequation_help_text)
    directory = models.ForeignKey(Directory)

    def __unicode__(self):
        return self.fullname

    def getquickstats(self):
        return self.directory.getquickstats()
    
def set_data(sender, instance, **kwargs):
    # create corresponding directory object
    instance.directory = Directory.objects.root.get_or_make_subdir(instance.code)

pre_save.connect(set_data, sender=Language)
