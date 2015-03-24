#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import locale

from django.db import models
from django.utils.translation import ugettext_lazy as _


class Notice(models.Model):
    directory = models.ForeignKey('pootle_app.Directory', db_index=True)
    message = models.TextField(_('Message'))
    added = models.DateTimeField(
        # Translators: The date that the news item was written
        _('Added'),
        auto_now_add=True,
        null=True,
        db_index=True,
    )

    class Meta:
        ordering = ["-added"]

    def __unicode__(self):
        return self.message

    def get_date(self):
        return self.added.strftime(locale.nl_langinfo(locale.D_T_FMT))
