# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.utils.functional import cached_property


class ItemDisplay(object):

    def __init__(self, section, item):
        self.section = section
        self.item = item

    def __str__(self):
        return "%s\n" % str(self.item)


class SectionDisplay(object):

    item_class = ItemDisplay

    def __init__(self, context, name):
        self.context = context
        self.name = name

    def __str__(self):
        description = ""
        if self.description:
            description = "%s\n" % self.description
        result = (
            "%s\n%s\n%s\n"
            % (self.title,
               "-" * len(self.title),
               description))
        for item in self:
            result += str(item)
        return "%s\n" % result

    @property
    def data(self):
        return self.context.context[self.name]

    def __iter__(self):
        failed = False
        if isinstance(self.data, (str, unicode)):
            failed = True
        try:
            iterable = iter(self.data)
        except TypeError:
            failed = True
        if failed:
            raise TypeError(
                "Invalid type (%s) for section '%s': "
                "context sections should be non-string iterables"
                % (type(self.data), self.name))
        for item in iterable:
            yield self.item_class(self, item)

    @cached_property
    def items(self):
        return list(self)

    @property
    def description(self):
        return self.info.get('description', "")

    @property
    def info(self):
        if self.context.context_info:
            info = self.context.context_info.get(self.name, {})
        else:
            info = {}
        if "title" not in info:
            info["title"] = self.name
        return info

    @property
    def title(self):
        return (
            "%s (%s)"
            % (self.info['title'], len(self.items)))


class Display(object):

    context_info = None
    section_class = SectionDisplay
    no_results_msg = ""

    def __init__(self, context):
        self.context = context

    def __str__(self):
        result = ""
        for section in self.sections:
            result += str(self.section(section))
        if not result:
            result = self.no_results_msg
        return "%s\n" % result

    @property
    def sections(self):
        return [
            section
            for section
            in self.context
            if self.context[section]]

    def section(self, section):
        return self.section_class(self, section)
