# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from django.core.exceptions import ValidationError

from allauth.account.adapter import get_adapter


@pytest.mark.django_db
def test_account_adapter_unicode():
    adapter = get_adapter()
    username = 'ascii'
    assert username == adapter.clean_username(username)
    username = u'lätin1'
    assert username == adapter.clean_username(username)
    with pytest.raises(ValidationError):  # Unicode characters don't yet pass.
        adapter.clean_username(u'อัตโนมัติ')
