#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import locale
from collections import OrderedDict

from django.conf import settings
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _

from pootle.core.cache import make_method_key
from pootle.core.mixins import TreeItem
from pootle.core.url_helpers import get_editor_filter
from pootle.i18n.gettext import tr_lang, language_dir


class LanguageManager(models.Manager):

    def get_queryset(self):
        """Mimics `select_related(depth=1)` behavior. Pending review."""
        return (
            super(LanguageManager, self).get_queryset().select_related(
                'directory',
            )
        )


class LiveLanguageManager(models.Manager):
    """Manager that only considers `live` languages.

    A live language is any language containing at least a project with
    translatable files.
    """
    def get_queryset(self):
        return super(LiveLanguageManager, self).get_queryset().filter(
                translationproject__isnull=False,
                project__isnull=True,
            ).distinct()

    def cached_dict(self, locale_code='en-us'):
        """Retrieves a sorted list of live language codes and names.

        :param locale_code: the UI locale for which language full names need to
            be localized.
        :return: an `OrderedDict`
        """
        key = make_method_key(self, 'cached_dict', locale_code)
        languages = cache.get(key, None)
        if languages is None:
            languages = OrderedDict(
                sorted([(lang[0], tr_lang(lang[1]))
                        for lang in self.values_list('code', 'fullname')],
                        cmp=locale.strcoll,
                        key=lambda x: x[1])
            )
            cache.set(key, languages, settings.POOTLE_CACHE_TIMEOUT)

        return languages


class Language(models.Model, TreeItem):

    code_help_text = _('ISO 639 language code for the language, possibly '
            'followed by an underscore (_) and an ISO 3166 country code. '
            '<a href="http://www.w3.org/International/articles/language-tags/">'
            'More information</a>')
    code = models.CharField(max_length=50, null=False, unique=True,
            db_index=True, verbose_name=_("Code"), help_text=code_help_text)
    fullname = models.CharField(max_length=255, null=False,
            verbose_name=_("Full Name"))

    specialchars_help_text = _('Enter any special characters that users '
            'might find difficult to type')
    specialchars = models.CharField(max_length=255, blank=True,
            verbose_name=_("Special Characters"),
            help_text=specialchars_help_text)

    plurals_help_text = _('For more information, visit '
            '<a href="http://docs.translatehouse.org/projects/'
            'localization-guide/en/latest/l10n/pluralforms.html">'
            'our page</a> on plural forms.')
    nplural_choices = (
            (0, _('Unknown')), (1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6)
    )
    nplurals = models.SmallIntegerField(default=0, choices=nplural_choices,
            verbose_name=_("Number of Plurals"), help_text=plurals_help_text)
    pluralequation = models.CharField(max_length=255, blank=True,
            verbose_name=_("Plural Equation"), help_text=plurals_help_text)

    directory = models.OneToOneField('pootle_app.Directory', db_index=True,
            editable=False)

    objects = LanguageManager()
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

    def delete(self, *args, **kwargs):
        directory = self.directory
        super(Language, self).delete(*args, **kwargs)
        directory.delete()

    def get_absolute_url(self):
        return reverse('pootle-language-browse', args=[self.code])

    def get_translate_url(self, **kwargs):
        return u''.join([
            reverse('pootle-language-translate', args=[self.code]),
            get_editor_filter(**kwargs),
        ])

    def clean(self):
        super(Language, self).clean()

        if self.fullname:
            self.fullname = self.fullname.strip()

    ### TreeItem

    def get_children(self):
        return self.translationproject_set.live()

    def get_cachekey(self):
        return self.directory.pootle_path

    ### /TreeItem

    def get_stats_for_user(self, user):
        self.set_children(self.get_children_for_user(user))

        return self.get_stats()

    def get_children_for_user(self, user):
        translation_projects = self.translationproject_set \
                                   .for_user(user) \
                                   .order_by('project__fullname')
        user_tps = filter(lambda x: x.is_accessible_by(user),
                          translation_projects)

        return user_tps


@receiver([post_delete, post_save])
def invalidate_language_list_cache(sender, instance, **kwargs):
    # XXX: maybe use custom signals or simple function calls?
    if instance.__class__.__name__ not in ['Language', 'TranslationProject']:
        return

    key = make_method_key('LiveLanguageManager', 'cached_dict', '*')
    cache.delete_pattern(key)
