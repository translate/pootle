# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from translate.filters.decorators import Category
from translate.storage import base

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models

from pootle.core.mixins import CachedTreeItem
from pootle.core.storage import PootleFileSystemStorage
from pootle.core.user import get_system_user, get_system_user_id
from pootle.core.utils.timezone import datetime_min
from pootle.i18n.gettext import ugettext_lazy as _
from pootle_format.models import Format
from pootle_statistics.models import SubmissionTypes

from .constants import NEW, UNTRANSLATED
from .fields import MultiStringField, TranslationStoreField
from .managers import StoreManager
from .validators import validate_no_slashes


# Needed to alter storage location in tests
fs = PootleFileSystemStorage()


class AbstractUnitChange(models.Model):

    class Meta(object):
        abstract = True

    unit = models.OneToOneField(
        "pootle_store.Unit",
        db_index=True,
        null=False,
        blank=False,
        related_name="change",
        on_delete=models.CASCADE)

    changed_with = models.IntegerField(
        null=False,
        blank=False,
        db_index=True)

    # unit translator
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        related_name='submitted',
        db_index=True,
        on_delete=models.SET(get_system_user))
    submitted_on = models.DateTimeField(db_index=True, null=True)

    commented_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        related_name='commented',
        db_index=True,
        on_delete=models.SET(get_system_user))
    commented_on = models.DateTimeField(db_index=True, null=True)

    # reviewer: who has accepted suggestion or removed FUZZY
    # None if translation has been submitted by approved translator
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='reviewed',
        null=True,
        db_index=True,
        on_delete=models.SET(get_system_user))
    reviewed_on = models.DateTimeField(db_index=True, null=True)


class AbstractUnitSource(models.Model):

    class Meta(object):
        abstract = True

    unit = models.OneToOneField(
        "pootle_store.Unit",
        db_index=True,
        null=False,
        blank=False,
        related_name="unit_source",
        on_delete=models.CASCADE)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=False,
        blank=False,
        db_index=True,
        related_name='created_units',
        default=get_system_user_id,
        on_delete=models.SET(get_system_user))

    created_with = models.IntegerField(
        null=False,
        blank=False,
        default=SubmissionTypes.SYSTEM,
        db_index=True)

    creation_revision = models.IntegerField(
        null=False,
        default=0,
        db_index=True,
        blank=True)

    source_hash = models.CharField(
        null=True,
        max_length=32,
        editable=False)

    source_wordcount = models.SmallIntegerField(
        default=0,
        editable=False)

    source_length = models.SmallIntegerField(
        default=0,
        editable=False)


class AbstractUnit(models.Model, base.TranslationUnit):

    store = models.ForeignKey(
        "pootle_store.Store",
        db_index=False,
        on_delete=models.CASCADE)

    index = models.IntegerField(db_index=True)
    unitid = models.TextField(editable=False)
    unitid_hash = models.CharField(max_length=32, db_index=True,
                                   editable=False)

    source_f = MultiStringField(null=True)
    target_f = MultiStringField(null=True, blank=True)
    target_wordcount = models.SmallIntegerField(default=0, editable=False)
    target_length = models.SmallIntegerField(db_index=True, default=0,
                                             editable=False)

    developer_comment = models.TextField(null=True, blank=True)
    translator_comment = models.TextField(null=True, blank=True)
    locations = models.TextField(null=True, editable=False)
    context = models.TextField(null=True, editable=False)

    state = models.IntegerField(null=False, default=UNTRANSLATED,
                                db_index=True)
    revision = models.IntegerField(null=False, default=0, db_index=True,
                                   blank=True)

    # Metadata
    creation_time = models.DateTimeField(auto_now_add=True, db_index=True,
                                         editable=False, null=True)
    mtime = models.DateTimeField(auto_now=True, db_index=True, editable=False)

    class Meta(object):
        abstract = True


class AbstractQualityCheck(models.Model):
    """Database cache of results of qualitychecks on unit."""

    class Meta(object):
        abstract = True

    name = models.CharField(max_length=64, db_index=True)
    unit = models.ForeignKey(
        "pootle_store.Unit",
        db_index=True,
        on_delete=models.CASCADE)
    category = models.IntegerField(null=False, default=Category.NO_CATEGORY)
    message = models.TextField()
    false_positive = models.BooleanField(default=False, db_index=True)


class AbstractStore(models.Model, CachedTreeItem, base.TranslationStore):

    file = TranslationStoreField(
        max_length=255,
        storage=fs,
        db_index=True,
        null=False,
        editable=False)

    parent = models.ForeignKey(
        'pootle_app.Directory',
        related_name='child_stores',
        editable=False,
        db_index=False,
        on_delete=models.CASCADE)

    translation_project_fk = 'pootle_translationproject.TranslationProject'
    translation_project = models.ForeignKey(
        translation_project_fk,
        related_name='stores',
        editable=False,
        db_index=False,
        on_delete=models.CASCADE)

    filetype = models.ForeignKey(
        Format,
        related_name='stores',
        null=True,
        blank=True,
        db_index=True,
        on_delete=models.CASCADE)
    is_template = models.BooleanField(default=False)

    # any changes to the `pootle_path` field may require updating the schema
    # see migration 0007_case_sensitive_schema.py
    pootle_path = models.CharField(
        max_length=255,
        null=False,
        unique=True,
        db_index=True,
        verbose_name=_("Path"))

    tp_path = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        db_index=True,
        verbose_name=_("Path"))
    # any changes to the `name` field may require updating the schema
    # see migration 0007_case_sensitive_schema.py
    name = models.CharField(
        max_length=128,
        null=False,
        editable=False,
        validators=[validate_no_slashes])

    file_mtime = models.DateTimeField(default=datetime_min)
    state = models.IntegerField(
        null=False,
        default=NEW,
        editable=False,
        db_index=True)
    creation_time = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        editable=False,
        null=True)
    last_sync_revision = models.IntegerField(
        db_index=True,
        null=True,
        blank=True)
    obsolete = models.BooleanField(default=False)

    # this is calculated from virtualfolders if installed and linked
    priority = models.FloatField(
        db_index=True,
        default=1,
        validators=[MinValueValidator(0)])

    objects = StoreManager()

    class Meta(object):
        ordering = ['pootle_path']
        index_together = [
            ["translation_project", "is_template"],
            ["translation_project", "pootle_path", "is_template", "filetype"]]
        unique_together = (
            ('parent', 'name'),
            ("obsolete", "translation_project", "tp_path"))
        base_manager_name = "objects"
        abstract = True


class AbstractSuggestion(models.Model, base.TranslationUnit):
    """Abstract suggestion"""

    class Meta(object):
        abstract = True

    target_f = MultiStringField()
    target_hash = models.CharField(max_length=32, db_index=True)
    unit = models.ForeignKey('pootle_store.Unit', on_delete=models.CASCADE)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=False,
        related_name='suggestions',
        db_index=True,
        on_delete=models.SET(get_system_user))
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        related_name='reviews',
        db_index=True,
        on_delete=models.SET(get_system_user))

    creation_time = models.DateTimeField(db_index=True, null=True)
    review_time = models.DateTimeField(null=True, db_index=True)

    state = models.ForeignKey(
        "pootle_store.SuggestionState",
        null=True,
        related_name='suggestions',
        db_index=True,
        on_delete=models.SET_NULL)


class AbstractSuggestionState(models.Model):
    """Database cache of results of qualitychecks on unit."""

    class Meta(object):
        abstract = True

    name = models.CharField(
        max_length=16,
        null=False,
        db_index=True)
