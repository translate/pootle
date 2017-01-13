# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.


class FSException(Exception):

    def __init__(self, message):
        super(Exception, self).__init__(message)
        self.message = message


class FSFetchError(FSException):
    pass


class FSAddError(FSException):
    pass


class FSStateError(FSException):
    pass


class FSSyncError(FSException):
    pass
