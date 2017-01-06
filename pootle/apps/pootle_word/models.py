# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.db import models

from pootle_store.models import Unit

from .abstracts import AbstractStem


class UnitStem(models.Model):

    class Meta(AbstractStem.Meta):
        unique_together = ["stem", "unit"]

    stem = models.ForeignKey("Stem")
    unit = models.ForeignKey(Unit)


class Stem(AbstractStem):

    units = models.ManyToManyField(
        Unit,
        through="UnitStem",
        related_name="stems")

    class Meta(AbstractStem.Meta):
        db_table = "pootle_word_stem"

    def __unicode__(self):
        return (
            "\"%s\", units: %s"
            % (self.root,
               list(self.units.values_list("id", flat=True))))
