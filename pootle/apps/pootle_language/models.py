# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from collections import OrderedDict

from translate.lang.data import get_language_iso_fullname

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import translation
from django.utils.functional import cached_property

from pootle.core.delegate import data_tool, language_code, site_languages
from pootle.core.mixins import TreeItem
from pootle.core.url_helpers import get_editor_filter
from pootle.i18n.gettext import language_dir, tr_lang, ugettext_lazy as _
from staticpages.models import StaticPage


class Language(models.Model, TreeItem):

    # any changes to the `code` field may require updating the schema
    # see migration 0002_case_insensitive_schema.py
    code = models.CharField(
        max_length=50, null=False, unique=True, db_index=True,
        verbose_name=_("Code"),
        help_text=_('ISO 639 language code for the language, possibly '
                    'followed by an underscore (_) and an ISO 3166 country '
                    'code. <a href="http://www.w3.org/International/'
                    'articles/language-tags/">More information</a>')
    )
    fullname = models.CharField(max_length=255, null=False,
                                verbose_name=_("Full Name"))

    specialchars = models.CharField(
        max_length=255, blank=True, verbose_name=_("Special Characters"),
        help_text=_('Enter any special characters that users might find '
                    'difficult to type')
    )

    plurals_help_text = _('For more information, visit '
                          '<a href="http://docs.translatehouse.org/projects/'
                          'localization-guide/en/latest/l10n/'
                          'pluralforms.html">'
                          'our page</a> on plural forms.')
    nplural_choices = (
        (0, _('Unknown')), (1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6)
    )
    nplurals = models.SmallIntegerField(
        default=0, choices=nplural_choices,
        verbose_name=_("Number of Plurals"), help_text=plurals_help_text
    )
    pluralequation = models.CharField(
        max_length=255, blank=True, verbose_name=_("Plural Equation"),
        help_text=plurals_help_text)

    directory = models.OneToOneField('pootle_app.Directory', db_index=True,
                                     editable=False, on_delete=models.CASCADE)

    objects = models.Manager()

    class Meta(object):
        ordering = ['code']
        db_table = 'pootle_app_language'

    # # # # # # # # # # # # # #  Properties # # # # # # # # # # # # # # # # # #

    @cached_property
    def data_tool(self):
        return data_tool.get(self.__class__)(self)

    @property
    def pootle_path(self):
        return '/%s/' % self.code

    @property
    def name(self):
        """localised ISO name for the language or fullname
        if request lang == server lang, and fullname is set. Uses code
        as the ultimate fallback
        """
        site_langs = site_languages.get()
        server_code = language_code.get()(settings.LANGUAGE_CODE)
        request_code = language_code.get()(translation.get_language())
        use_db_name = (
            not translation.get_language()
            or (self.fullname
                and server_code.matches(request_code)))
        if use_db_name:
            return self.fullname
        iso_name = get_language_iso_fullname(self.code) or self.fullname
        return (
            site_langs.capitalize(tr_lang(iso_name))
            if iso_name
            else self.code)

    @property
    def direction(self):
        """Return the language direction."""
        return language_dir(self.code)

    # # # # # # # # # # # # # #  Methods # # # # # # # # # # # # # # # # # # #

    @classmethod
    def get_canonical(cls, language_code):
        """Returns the canonical `Language` object matching `language_code`.

        If no language can be matched, `None` will be returned.

        :param language_code: the code of the language to retrieve.
        """
        qs = cls.objects.select_related("directory")
        try:
            return qs.get(code__iexact=language_code)
        except cls.DoesNotExist:
            _lang_code = language_code
            if "-" in language_code:
                _lang_code = language_code.replace("-", "_")
            elif "_" in language_code:
                _lang_code = language_code.replace("_", "-")
            try:
                return qs.get(code__iexact=_lang_code)
            except cls.DoesNotExist:
                return None

    def __unicode__(self):
        return u"%s - %s" % (self.name, self.code)

    def __init__(self, *args, **kwargs):
        super(Language, self).__init__(*args, **kwargs)

    def save(self, *args, **kwargs):
        # create corresponding directory object
        from pootle_app.models.directory import Directory
        self.directory = Directory.objects.root.get_or_make_subdir(self.code)

        # Do not repeat special chars.
        self.specialchars = u"".join(
            OrderedDict([
                ((specialchar
                  if isinstance(specialchar, unicode)
                  else specialchar.decode("unicode_escape")),
                 None)
                for specialchar
                in self.specialchars]).keys())
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

    # # # TreeItem

    def get_children(self):
        return self.translationproject_set.live()

    # # # /TreeItem

    def get_children_for_user(self, user, select_related=None):
        return self.translationproject_set.for_user(
            user, select_related=select_related
        ).select_related(
            "project"
        ).order_by('project__fullname')

    def get_announcement(self, user=None):
        """Return the related announcement, if any."""
        return StaticPage.get_announcement_for(self.pootle_path, user)
