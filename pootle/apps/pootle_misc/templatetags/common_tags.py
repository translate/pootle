# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import datetime

from django import template
from django.utils.translation import get_language

from pootle.i18n import formatter
from pootle.i18n.dates import timesince
from pootle.i18n.gettext import ugettext_lazy as _


register = template.Library()


@register.filter
def time_since(timestamp):
    return (
        timesince(
            timestamp, locale=get_language())
        if timestamp
        else "")


@register.inclusion_tag('includes/avatar.html')
def avatar(username, email_hash, size):
    # TODO: return sprite if its a system user
    if username == "system":
        return dict(icon="icon-pootle")
    return dict(
        avatar_url=(
            'https://secure.gravatar.com/avatar/%s?s=%d&d=mm'
            % (email_hash, size)))


@register.inclusion_tag('browser/_progressbar.html')
def progress_bar(total, fuzzy, translated):
    if not total:
        fuzzy_frac = translated_frac = untranslated_frac = 0
        cldrformat = "0%"
    else:
        untranslated = total - translated - fuzzy
        untranslated_frac = float(untranslated)/total
        fuzzy_frac = float(fuzzy)/total
        translated_frac = float(translated)/total
        cldrformat = "#,##0.0%"
    untranslated_display = (_("{percentage} untranslated")).format(
        percentage=formatter.percent(untranslated_frac, cldrformat))
    fuzzy_display = (_("{percentage} needs work")).format(
        percentage=formatter.percent(fuzzy_frac, cldrformat))
    translated_display = (_("{percentage} translated")).format(
        percentage=formatter.percent(translated_frac, cldrformat))
    return dict(
        untranslated_percent_display=untranslated_display,
        fuzzy_percent_display=fuzzy_display,
        translated_percent_display=translated_display,
        untranslated_bar=round(untranslated_frac * 100, 1),
        fuzzy_bar=round(fuzzy_frac * 100, 1),
        translated_bar=round(translated_frac * 100, 1))


@register.inclusion_tag('browser/_table.html')
def display_table(table, can_translate):
    return {
        'can_translate': can_translate,
        'table': table,
    }


@register.filter
@template.defaultfilters.stringfilter
def cssid(value):
    """Replaces all '.', '+', ' ' and '@' with '-'.

    Used to create valid CSS identifiers from tree item codes.
    """
    return value.replace(u'.', u'-').replace(u'@', u'-') \
                .replace(u'+', u'-').replace(u' ', u'-')


@register.filter
def endswith(value, arg):
    return value.endswith(arg)


@register.filter
def count(value, arg):
    return value.count(arg)


@register.filter
def label_tag(field, suffix=None):
    """Returns the `label_tag` for a field.

    Optionally allows overriding the default `label_suffix` for the form
    this field belongs to.
    """
    if not hasattr(field, 'label_tag'):
        return ''

    return field.label_tag(label_suffix=suffix)


@register.inclusion_tag('core/_top_scorers.html')
def top_scorers(user, top_scorers):
    return dict(user=user, top_scorers=top_scorers)


@register.simple_tag
def format_date_range(date_from, date_to, separator=" - ",
                      format_str="{dt:%B} {dt.day}, {dt:%Y}",
                      year_f=", {dt:%Y}", month_f="{dt:%B}"):
    """Takes a start date, end date, separator and formatting strings and
    returns a pretty date range string
    """
    if (isinstance(date_to, datetime.datetime) and
        isinstance(date_from, datetime.datetime)):
        date_to = date_to.date()
        date_from = date_from.date()

    if date_to and date_to != date_from:
        from_format = to_format = format_str
        if date_from.year == date_to.year:
            from_format = from_format.replace(year_f, '')
            if date_from.month == date_to.month:
                to_format = to_format.replace(month_f, '')
        return separator.join((from_format.format(dt=date_from),
                               to_format.format(dt=date_to)))

    return format_str.format(dt=date_from)
