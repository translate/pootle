# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import logging


logger = logging.getLogger(__name__)


class ItemResponse(object):

    def __init__(self, response, action_type, complete=True, msg=None, **kwargs):
        self.response = response
        self.action_type = action_type
        self.complete = complete
        self.msg = msg or ""
        self.kwargs = kwargs

    def __str__(self):
        extra = ""
        if self.failed:
            extra = " FAILED"
        if self.msg:
            extra = "%s %s" % (extra, self.msg)
        if self.kwargs:
            extra = "%s %s" % (extra, str(self.kwargs))
        return (
            "<%s(%s): %s%s>"
            % (self.__class__.__name__,
               self.response,
               self.action_type,
               extra))

    @property
    def failed(self):
        return not self.complete


class Response(object):

    __responses__ = None
    response_class = ItemResponse

    def __init__(self, context):
        self.context = context
        self.__responses__ = {}
        self.clear_cache()

    def __getitem__(self, k):
        return self.__responses__[k]

    def __iter__(self):
        for k in self.__responses__:
            if self.__responses__[k]:
                yield k

    def __len__(self):
        return len([x for x in self.__iter__()])

    def __str__(self):
        failed = ""
        if self.has_failed:
            failed = "FAIL "
        if self.made_changes:
            return (
                "<%s(%s): %s%s>"
                % (self.__class__.__name__,
                   self.context,
                   failed,
                   self.success))
        return (
            "<%s(%s): %sNo changes made>"
            % (self.__class__.__name__,
               self.context,
               failed))

    @property
    def has_failed(self):
        return len(list(self.failed())) > 0

    @property
    def made_changes(self):
        return len(list(self.completed())) > 0

    @property
    def response_types(self):
        return self.__responses__.keys()

    @property
    def success(self):
        return ', '.join(
            ["%s: %s" % (k, len(list(self.completed(k))))
             for k in self.response_types
             if len(list(self.completed(k)))])

    def add(self, response_type, complete=True, msg=None, **kwargs):
        response = self.response_class(
            self, response_type, complete=complete, msg=msg, **kwargs)
        if response_type not in self.__responses__:
            self.__responses__[response_type] = []
        self.__responses__[response_type].append(response)
        return response

    def clear_cache(self):
        for k in self.response_types:
            self.__responses__[k] = []

    def completed(self, *response_types):
        response_types = response_types or self.response_types
        for response_type in response_types:
            for response in self.__responses__[response_type]:
                if not response.failed:
                    yield response

    def failed(self, *response_types):
        response_types = response_types or self.response_types
        for response_type in response_types:
            for response in self.__responses__[response_type]:
                if response.failed:
                    yield response
