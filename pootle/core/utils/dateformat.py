# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.


from django.utils import timezone
from django.utils.dateformat import DateFormat as DjangoDateFormat


class DateFormat(DjangoDateFormat):

    def c(self):
        return self.data.isoformat(' ')


def format(value, format_string='c'):
    df = DateFormat(timezone.localtime(value))
    return df.format(format_string)
