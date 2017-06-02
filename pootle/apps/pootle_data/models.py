# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.db import models

from .abstracts import AbstractPootleChecksData, AbstractPootleData


class StoreData(AbstractPootleData):

    class Meta(object):
        db_table = "pootle_store_data"

    store = models.OneToOneField(
        "pootle_store.Store",
        on_delete=models.CASCADE,
        db_index=True,
        related_name="data")

    def __unicode__(self):
        return self.store.pootle_path


class StoreChecksData(AbstractPootleChecksData):

    class Meta(AbstractPootleChecksData.Meta):
        db_table = "pootle_store_check_data"
        unique_together = ["store", "category", "name"]
        index_together = [AbstractPootleChecksData.Meta.index_together]

    store = models.ForeignKey(
        "pootle_store.Store",
        on_delete=models.CASCADE,
        db_index=False,
        related_name="check_data")

    def __unicode__(self):
        return self.store.pootle_path


class TPData(AbstractPootleData):

    class Meta(object):
        db_table = "pootle_tp_data"

    tp = models.OneToOneField(
        "pootle_translationproject.TranslationProject",
        on_delete=models.CASCADE,
        db_index=True,
        related_name="data")

    def __unicode__(self):
        return self.tp.pootle_path


class TPChecksData(AbstractPootleChecksData):

    class Meta(AbstractPootleChecksData.Meta):
        db_table = "pootle_tp_check_data"
        unique_together = ["tp", "category", "name"]
        index_together = [AbstractPootleChecksData.Meta.index_together]

    tp = models.ForeignKey(
        "pootle_translationproject.TranslationProject",
        on_delete=models.CASCADE,
        db_index=False,
        related_name="check_data")

    def __unicode__(self):
        return self.tp.pootle_path
