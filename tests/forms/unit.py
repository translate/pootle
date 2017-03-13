# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from django.forms import Form

from translate.misc import multistring

from pootle_app.models.permissions import get_matching_permissions
from pootle_store.forms import (
    MultiStringFormField, MultiStringWidget, unit_form_factory)


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


@pytest.mark.django_db
def test_submit_no_source(rf, po_directory, default, store0):
    """Tests that the source string cannot be modified."""
    language = store0.translation_project.language
    unit = store0.units[0]
    source_string = unit.source_f
    directory = unit.store.parent
    post_dict = {
        'id': unit.id,
        'index': unit.index,
        'source_f_0': 'altered source string',
        'target_f_0': 'dummy',
    }

    request = _create_post_request(rf, directory, data=post_dict, user=default)
    form = _create_unit_form(request, language, unit)

    assert form.is_valid()
    form.save()

    unit = store0.units[0]
    assert unit.source_f == source_string
    assert unit.target_f == 'dummy'


@pytest.mark.django_db
def test_submit_fuzzy(rf, po_directory, admin, default, store0):
    """Tests that non-admin users can't set the fuzzy flag."""
    language = store0.translation_project.language
    unit = store0.units[0]
    directory = unit.store.parent
    post_dict = {
        'id': unit.id,
        'index': unit.index,
        'target_f_0': unit.target_f,
        'is_fuzzy': True,
    }

    request = _create_post_request(rf, directory, data=post_dict, user=admin)
    admin_form = _create_unit_form(request, language, unit)
    assert admin_form.is_valid()

    request = _create_post_request(rf, directory, data=post_dict, user=default)
    user_form = _create_unit_form(request, language, unit)
    assert not user_form.is_valid()
    assert 'is_fuzzy' in user_form.errors


@pytest.mark.parametrize('nplurals, decompressed_value', [
    (1, [None]),
    (2, [None, None]),
    (3, [None, None, None]),
    (4, [None, None, None, None]),
])
def test_multistringwidget_decompress_none(nplurals, decompressed_value):
    """Tests unit's `MultiStringWidget` decompresses None values."""
    widget = MultiStringWidget(nplurals=nplurals)
    assert widget.decompress(None) == decompressed_value


@pytest.mark.parametrize('value', [
    ['foo\\bar'],
    ['foö\r\nbär'],
    ['foö\\r\\nbär'],
    ['foö\r\n\\r\\nbär', 'bär\r\n\\r\\nbäz'],
    ['nfoö\nbär'],
    ['nfoö\\nbär'],
    ['foö\n\\nbär', 'bär\n\\nbäz'],
])
def test_multistringwidget_decompress_list_of_values(value):
    """Tests unit's `MultiStringWidget` decompresses a list of values."""
    widget = MultiStringWidget()
    assert widget.decompress(value) == value


@pytest.mark.parametrize('value', [
    'foo\\bar',
    'foö\r\nbär',
    'foö\\r\\nbär',
    'foö\r\n\\r\\nbär',
    'nfoö\nbär',
    'nfoö\\nbär',
    'foö\n\\nbär',
])
def test_multistringwidget_decompress_strings(value):
    """Tests unit's `MultiStringWidget` decompresses string values."""
    widget = MultiStringWidget()
    assert widget.decompress(value) == [value]


@pytest.mark.parametrize('value', [
    'foo\\bar',
    'foö\r\nbär',
    'foö\\r\\nbär',
    'foö\r\n\\r\\nbär',
    'nfoö\nbär',
    'nfoö\\nbär',
    'foö\n\\nbär',
    ['foo\\bar'],
    ['foö\r\nbär'],
    ['foö\\r\\nbär'],
    ['foö\r\n\\r\\nbär', 'bär\r\n\\r\\nbäz'],
    ['nfoö\nbär'],
    ['nfoö\\nbär'],
    ['foö\n\\nbär', 'bär\n\\nbäz'],
])
def test_multistringwidget_decompress_multistrings(value):
    """Tests unit's `MultiStringWidget` decompresses string values."""
    widget = MultiStringWidget()
    expected_value = [value] if isinstance(value, basestring) else value
    assert widget.decompress(multistring.multistring(value)) == expected_value


@pytest.mark.parametrize('value', [
    [u'foo\\bar'],
    [u"\t foo\\bar\n"],
    [u'foö\r\nbär'],
    [u'foö\\r\\nbär'],
    [u'foö\r\n\\r\\nbär', u'bär\r\n\\r\\nbäz'],
    [u'nfoö\nbär'],
    [u'nfoö\\nbär'],
    [u'foö\n\\nbär', u'bär\n\\nbäz'],
])
def test_form_multistringformfield(value):
    """Tests `MultiStringFormField`'s value compression in a form."""
    def test_form_factory(nplurals):
        class TestForm(Form):
            value = MultiStringFormField(nplurals=nplurals)

        return TestForm

    data = {'value_%d' % i: val for i, val in enumerate(value)}
    form_class = test_form_factory(nplurals=len(value))
    form = form_class(data=data)
    assert form.is_valid()
    assert form.cleaned_data == {'value': value}
