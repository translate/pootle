# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import logging

import pytest

from django.core.management import call_command
from django.core.management.base import CommandError


@pytest.mark.cmd
@pytest.mark.parametrize('month', ['12-2012', '12-12', '12', '12/2012', '2012/12'])
def test_generate_invoices_invalid_debug_month(month):
    with pytest.raises(CommandError) as e:
        call_command('generate_invoices', '--debug-month=%s' % month)
    assert 'month parameter has an invalid format' in str(e)


@pytest.mark.cmd
@pytest.mark.django_db
def test_generate_invoices_nonexistant_user(settings):
    settings.POOTLE_INVOICES_RECIPIENTS = {
        'bogus_member': {},
    }
    with pytest.raises(CommandError) as e:
        call_command('generate_invoices')
    assert 'User bogus_member not found.' in str(e)
