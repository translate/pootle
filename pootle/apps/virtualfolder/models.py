# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _

from pootle.core.delegate import data_tool
from pootle.core.markup import MarkupField, get_markup_filter_display_name
from pootle_app.models import Directory
from pootle_data.abstracts import AbstractPootleData
from pootle_language.models import Language
from pootle_project.models import Project
from pootle_store.models import Store

from .delegate import path_matcher


class VirtualFolder(models.Model):

    # any changes to the `name` field may require updating the schema
    # see migration 0003_case_sensitive_schema.py
    name = models.CharField(_('Name'), blank=False, max_length=70)

    filter_rules = models.TextField(
        # Translators: This is a noun.
        _('Filter'),
        blank=False,
        help_text=_('Filtering rules that tell which stores this virtual '
                    'folder comprises.'),
    )
    priority = models.FloatField(
        _('Priority'),
        default=1,
        help_text=_('Number specifying importance. Greater priority means it '
                    'is more important.'),
    )
    is_public = models.BooleanField(
        _('Is public?'),
        default=True,
        help_text=_('Whether this virtual folder is public or not.'),
    )
    description = MarkupField(
        _('Description'),
        blank=True,
        help_text=_('Use this to provide more information or instructions. '
                    'Allowed markup: %s', get_markup_filter_display_name()),
    )
    stores = models.ManyToManyField(
        Store,
        db_index=True,
        related_name='vfolders')
    project = models.ForeignKey(
        Project,
        null=True,
        blank=True,
        db_index=True,
        related_name="vfolders")
    language = models.ForeignKey(
        Language,
        null=True,
        blank=True,
        db_index=True,
        related_name="vfolders")

    @cached_property
    def path_matcher(self):
        return path_matcher.get(self.__class__)(self)

    @cached_property
    def data_tool(self):
        return data_tool.get(self.__class__)(self)

    def __unicode__(self):
        name = self.name
        if self.language:
            ("%s, language=%s"
             % (name, self.language.code))
        if self.project:
            ("%s, project=%s"
             % (name, self.project.code))
        return name

    def save(self, *args, **kwargs):
        # Force validation of fields.
        self.clean_fields()
        self.name = self.name.lower()
        super(VirtualFolder, self).save(*args, **kwargs)

    def clean_fields(self):
        """Validate virtual folder fields."""
        if self.priority <= 0:
            raise ValidationError(u'Priority must be greater than zero.')

        if not self.filter_rules:
            raise ValidationError(u'Some filtering rule must be specified.')
        try:
            matching_directory = Directory.objects.get(
                pootle_path__regex="%s/%s/$"
                % (self.path_matcher.path, self.name))
        except Directory.DoesNotExist:
            return
        except Directory.MultipleObjectsReturned:
            raise ValidationError(
                (u"Problem adding virtual folder '%s': "
                 u"VirtualFolderTreeItem clashes with existing Directories"
                 % (self.name)))
        raise ValidationError(
            (u"Problem adding virtual folder '%s': "
             u"VirtualFolderTreeItem clashes with Directory %s"
             % (self.name,
                matching_directory.pootle_path)))


class VFData(AbstractPootleData):

    class Meta(object):
        db_table = "pootle_vf_data"

    vf = models.OneToOneField(
        "virtualfolder.VirtualFolder",
        db_index=True,
        related_name="data")

    def __unicode__(self):
        return unicode(self.vf)
