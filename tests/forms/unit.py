#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2014 Evernote Corporation
#
# This file is part of Pootle.
#
# Pootle is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.

import pytest

from pootle_app.models.permissions import get_matching_permissions
from pootle_store.util import FUZZY, TRANSLATED, UNTRANSLATED
from pootle_store.forms import unit_form_factory, UnitStateField


def _create_post_request(rf, directory, user, url='/', data=None):
    """Convenience function to create and setup fake POST requests."""
    if data is None:
        data = {}

    request = rf.post(url, data=data)
    request.user = user
    request.permissions = get_matching_permissions(request.user, directory)
    return request


def _create_unit_form(request, language, unit):
    """Convenience function to create unit forms."""
    form_class = unit_form_factory(language, request=request)
    return form_class(request.POST, instance=unit, request=request)


def test_submit_fuzzy(rf, admin, default, default_ps,
                      afrikaans, af_tutorial_po):
    """Tests that non-admin users can't set the fuzzy flag."""
    language = afrikaans
    unit = af_tutorial_po.getitem(0)
    directory = unit.store.parent
    post_dict = {
        'id': unit.id,
        'index': unit.index,
        'target_f_0': unit.target_f,
        'state': FUZZY,
    }

    request = _create_post_request(rf, directory, data=post_dict, user=admin)
    admin_form = _create_unit_form(request, language, unit)
    assert admin_form.is_valid()

    request = _create_post_request(rf, directory, data=post_dict, user=default)
    user_form = _create_unit_form(request, language, unit)
    assert not user_form.is_valid()
    assert 'state' in user_form.errors


def test_unit_state():
    """Tests how checkbox states (as strings) map to booleans."""
    field = UnitStateField(required=False)
    assert field.clean(str(FUZZY))
    assert field.clean(str(TRANSLATED))
    assert field.clean(str(UNTRANSLATED))
    assert field.clean(True)
    assert not field.clean('True')  # Unknown state value evaluates to False
    assert not field.clean(False)
    assert not field.clean('False')
