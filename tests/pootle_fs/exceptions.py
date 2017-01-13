# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.


from pootle_fs.exceptions import (
    FSAddError, FSFetchError, FSStateError, FSSyncError)


def test_error_fs_add():
    error = FSAddError("it went pear shaped")
    assert repr(error) == "FSAddError('it went pear shaped',)"
    assert str(error) == "it went pear shaped"
    assert error.message == "it went pear shaped"


def test_error_fs_fetch():
    error = FSFetchError("it went pear shaped")
    assert repr(error) == "FSFetchError('it went pear shaped',)"
    assert str(error) == "it went pear shaped"
    assert error.message == "it went pear shaped"


def test_error_fs_state():
    error = FSStateError("it went pear shaped")
    assert repr(error) == "FSStateError('it went pear shaped',)"
    assert str(error) == "it went pear shaped"
    assert error.message == "it went pear shaped"


def test_error_fs_sync():
    error = FSSyncError("it went pear shaped")
    assert repr(error) == "FSSyncError('it went pear shaped',)"
    assert str(error) == "it went pear shaped"
    assert error.message == "it went pear shaped"
