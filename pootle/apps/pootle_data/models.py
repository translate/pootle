# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.db import models
from django.utils import six

from .abstracts import AbstractPootleChecksData, AbstractPootleData


@six.python_2_unicode_compatible
class StoreData(AbstractPootleData):

    class Meta(object):
        db_table = "pootle_store_data"

    store = models.OneToOneField(
        "pootle_store.Store",
        on_delete=models.CASCADE,
        db_index=True,
        related_name="data")

    def __str__(self):
        return self.store.pootle_path


@six.python_2_unicode_compatible
class StoreChecksData(AbstractPootleChecksData):

    class Meta(AbstractPootleChecksData.Meta):
        db_table = "pootle_store_check_data"
        unique_together = ["store", "category", "name"]
        index_together = (
            [AbstractPootleChecksData.Meta.index_together]
            + [["store", "category", "name"]])

    store = models.ForeignKey(
        "pootle_store.Store",
        on_delete=models.CASCADE,
        db_index=True,
        related_name="check_data")

    def __str__(self):
        return self.store.pootle_path


@six.python_2_unicode_compatible
class TPData(AbstractPootleData):

    class Meta(object):
        db_table = "pootle_tp_data"

    tp = models.OneToOneField(
        "pootle_translationproject.TranslationProject",
        on_delete=models.CASCADE,
        db_index=True,
        related_name="data")

    def __str__(self):
        return self.tp.pootle_path


@six.python_2_unicode_compatible
class TPChecksData(AbstractPootleChecksData):

    class Meta(AbstractPootleChecksData.Meta):
        db_table = "pootle_tp_check_data"
        unique_together = ["tp", "category", "name"]
        index_together = (
            [AbstractPootleChecksData.Meta.index_together]
            + [["tp", "category", "name"]])

    tp = models.ForeignKey(
        "pootle_translationproject.TranslationProject",
        on_delete=models.CASCADE,
        db_index=True,
        related_name="check_data")

    def __str__(self):
        return self.tp.pootle_path
