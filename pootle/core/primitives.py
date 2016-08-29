# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.


class PrefixedDict(object):

    def __init__(self, context, prefix):
        self.__context = context
        self.__prefix = prefix

    def __getitem__(self, k):
        return self.__context["%s%s" % (self.__prefix, k)]

    def __setitem__(self, k, v):
        self.__context["%s%s" % (self.__prefix, k)] = v

    def get(self, k, default=None):
        try:
            return self.__context["%s%s" % (self.__prefix, k)]
        except KeyError:
            return default
