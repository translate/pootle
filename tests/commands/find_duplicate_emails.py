# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from django.core.management import call_command


@pytest.mark.cmd
@pytest.mark.django_db
def test_find_duplicate_emails_nodups(capfd, no_extra_users):
    """No duplicates found.

    Standard users shouldn't flag any error.
    """
    call_command('find_duplicate_emails')
    out, err = capfd.readouterr()
    assert "There are no accounts with duplicate emails" in out


@pytest.mark.cmd
@pytest.mark.django_db
def test_find_duplicate_emails_noemails(capfd, member, member2):
    """User have no email set."""
    call_command('find_duplicate_emails')
    out, err = capfd.readouterr()
    assert "The following users have no email set" in out
    assert "member " in out
    assert "member2" in out


@pytest.mark.cmd
@pytest.mark.django_db
def test_find_duplicate_emails_withdups(capfd, member_with_email,
                                        member2_with_email):
    """Find duplicate emails for removal where we have dups.

    Standard users shouldn't flag any error.
    """
    member2_with_email.email = member_with_email.email
    member2_with_email.save()
    call_command('find_duplicate_emails')
    out, err = capfd.readouterr()
    assert "The following users have the email: member_with_email@this.test" in out
    assert "member_with_email" in out
    assert "member2_with_email" in out
