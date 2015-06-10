#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009-2013 Zuza Software Foundation
# Copyright 2013-2014 Evernote Corporation
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

from django.conf import settings
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.db import models
from django.utils.translation import ugettext_lazy as _

from pootle.core.managers import RelatedManager
from pootle.core.mixins import TreeItem
from pootle.core.url_helpers import get_editor_filter
from pootle.i18n.gettext import tr_lang, language_dir


# FIXME: Generate key dynamically
CACHE_KEY = 'pootle-languages'


class LiveLanguageManager(models.Manager):
    """Manager that only considers `live` languages.

    A live language is any language other than the special `Templates`
    language that have any project with translatable files and is not a
    source language.
    """
    def get_queryset(self):
        return super(LiveLanguageManager, self).get_queryset().filter(
                ~models.Q(code='templates'),
                translationproject__isnull=False,
                project__isnull=True,
            ).distinct()

    def cached(self):
        languages = cache.get(CACHE_KEY)
        if not languages:
            languages = self.all()
            cache.set(CACHE_KEY, languages, settings.OBJECT_CACHE_TIMEOUT)

        return languages


class Language(models.Model, TreeItem):

    code = models.CharField(
        max_length=50,
        null=False,
        unique=True,
        db_index=True,
        verbose_name=_("Code"),
        help_text=_('ISO 639 language code for the language, possibly '
                    'followed by an underscore (_) and an ISO 3166 country '
                    'code. <a href="http://www.w3.org/International/articles/'
                    'language-tags/">More information</a>'),
    )
    fullname = models.CharField(
        max_length=255,
        null=False,
        verbose_name=_("Full Name"),
    )
    specialchars = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Special Characters"),
        help_text=_('Enter any special characters that users might find '
                    'difficult to type'),
    )
    nplurals = models.SmallIntegerField(
        default=0,
        choices=(
            (0, _('Unknown')), (1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6)
        ),
        verbose_name=_("Number of Plurals"),
        help_text=_('For more information, visit <a href="'
                    'http://docs.translatehouse.org/projects/'
                    'localization-guide/en/latest/l10n/pluralforms.html">our '
                    'page</a> on plural forms.'),
    )
    pluralequation = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Plural Equation"),
        help_text=_('For more information, visit <a href="'
                    'http://docs.translatehouse.org/projects/'
                    'localization-guide/en/latest/l10n/pluralforms.html">our '
                    'page</a> on plural forms.'),
    )
    directory = models.OneToOneField(
        'pootle_app.Directory',
        db_index=True,
        editable=False,
    )

    objects = RelatedManager()
    live = LiveLanguageManager()

    class Meta:
        ordering = ['code']
        db_table = 'pootle_app_language'

    ############################ Properties ###################################

    @property
    def pootle_path(self):
        return '/%s/' % self.code

    @property
    def name(self):
        """Localized fullname for the language."""
        return tr_lang(self.fullname)

    ############################ Methods ######################################

    @property
    def direction(self):
        """Return the language direction."""
        return language_dir(self.code)

    def __unicode__(self):
        return u"%s - %s" % (self.name, self.code)

    def __init__(self, *args, **kwargs):
        super(Language, self).__init__(*args, **kwargs)

    def __repr__(self):
        return u'<%s: %s>' % (self.__class__.__name__, self.fullname)

    def save(self, *args, **kwargs):
        # create corresponding directory object
        from pootle_app.models.directory import Directory
        self.directory = Directory.objects.root.get_or_make_subdir(self.code)

        super(Language, self).save(*args, **kwargs)

        # FIXME: far from ideal, should cache at the manager level instead
        cache.delete(CACHE_KEY)

    def delete(self, *args, **kwargs):
        directory = self.directory
        super(Language, self).delete(*args, **kwargs)
        directory.delete()

        # FIXME: far from ideal, should cache at the manager level instead
        cache.delete(CACHE_KEY)

    def get_absolute_url(self):
        return reverse('pootle-language-overview', args=[self.code])

    def get_translate_url(self, **kwargs):
        return u''.join([
            reverse('pootle-language-translate', args=[self.code]),
            get_editor_filter(**kwargs),
        ])

    ### TreeItem

    def get_children(self):
        return self.translationproject_set.live()

    def get_cachekey(self):
        return self.directory.pootle_path

    ### /TreeItem

    def translated_percentage(self):
        total = max(self.get_total_wordcount(), 1)
        translated = self.get_translated_wordcount()
        return int(100.0 * translated / total)
