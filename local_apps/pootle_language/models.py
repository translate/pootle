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

from django.utils.translation import ugettext_lazy as _
from django.db                import models
from django.db.models.signals import pre_save, post_delete

from pootle.i18n.gettext import tr_lang, language_dir

from pootle_misc.util import getfromcache
from pootle_misc.baseurl import l
from pootle_store.util import statssum
from pootle_store.models import Unit
from pootle_app.lib.util import RelatedManager

class Language(models.Model):
    objects = RelatedManager()
    class Meta:
        ordering = ['code']
        db_table = 'pootle_app_language'

    code_help_text = _('ISO 639 language code for the language, possibly followed by an underscore (_) and an ISO 3166 country code. <a href="http://www.w3.org/International/articles/language-tags/">More information</a>')
    code           = models.CharField(max_length=50, null=False, unique=True, db_index=True, verbose_name=_("Code"), help_text=code_help_text)
    fullname       = models.CharField(max_length=255, null=False, verbose_name=_("Full Name"))

    specialchars_help_text = _('Enter any special characters that users might find difficult to type')
    specialchars   = models.CharField(max_length=255, blank=True, verbose_name=_("Special Characters"), help_text=specialchars_help_text)

    plurals_help_text = _('For more information, visit <a href="http://translate.sourceforge.net/wiki/l10n/pluralforms">our wiki page</a> on plural forms.')
    nplural_choices = ((0, _('Unknown')), (1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6))
    nplurals       = models.SmallIntegerField(default=0, choices=nplural_choices, verbose_name=_("Number of Plurals"), help_text=plurals_help_text)

    pluralequation = models.CharField(max_length=255, blank=True, verbose_name=_("Plural Equation"), help_text=plurals_help_text)
    directory = models.OneToOneField('pootle_app.Directory', db_index=True, editable=False)

    pootle_path = property(lambda self: '/%s/' % self.code)

    def __repr__(self):
        return u'<%s: %s>' % (self.__class__.__name__, self.fullname)

    def __unicode__(self):
        return u"%s - %s" % (self.localname(), self.code)

    def get_mtime(self):
        return Unit.objects.filter(store__translation_project__language=self).order_by('-mtime').values_list('mtime', flat=True)[0]

    @getfromcache
    def getquickstats(self):
        return statssum(self.translationproject_set.iterator())

    def get_absolute_url(self):
        return l(self.pootle_path)

    def localname(self):
        """localized fullname"""
        return tr_lang(self.fullname)

    def get_direction(self):
        """returns language direction"""
        return language_dir(self.code)

    def translated_percentage(self):
        return int(100.0 * self.getquickstats()['translatedsourcewords'] / max(self.getquickstats()['totalsourcewords'], 1))

def set_data(sender, instance, **kwargs):
    # create corresponding directory object
    from pootle_app.models.directory import Directory
    instance.directory = Directory.objects.root.get_or_make_subdir(instance.code)

pre_save.connect(set_data, sender=Language)

def delete_directory(sender, instance, **kwargs):
    instance.directory.delete()
post_delete.connect(delete_directory, sender=Language)
