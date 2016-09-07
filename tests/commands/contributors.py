# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from argparse import ArgumentTypeError
from collections import OrderedDict
from dateutil.parser import parse as parse_datetime
from email.utils import formataddr

import pytest
import pytz

from django.core.management import call_command
from django.core.management.base import CommandError

from pootle.core.utils.timezone import make_aware
from pootle_app.management.commands.contributors import get_aware_datetime
from pytest_pootle.fixtures.contributors import CONTRIBUTORS_WITH_EMAIL


def test_contributors_get_aware_datetime():
    """Get an aware datetime from a valid string."""
    iso_datetime = make_aware(parse_datetime("2016-01-24T23:15:22+0000"),
                              tz=pytz.utc)

    # Test ISO 8601 datetime.
    assert iso_datetime == get_aware_datetime("2016-01-24T23:15:22+0000",
                                              tz=pytz.utc)

    # Test git-like datetime.
    assert iso_datetime == get_aware_datetime("2016-01-24 23:15:22 +0000",
                                              tz=pytz.utc)

    # Test just an ISO 8601 date.
    iso_datetime = make_aware(parse_datetime("2016-01-24T00:00:00+0000"),
                              tz=pytz.utc)
    assert iso_datetime == get_aware_datetime("2016-01-24", tz=pytz.utc)

    # Test None.
    assert get_aware_datetime(None) is None

    # Test empty string.
    assert get_aware_datetime("") is None

    # Test non-empty string.
    with pytest.raises(ArgumentTypeError):
        get_aware_datetime("THIS FAILS")

    # Test blank string.
    with pytest.raises(ArgumentTypeError):
        get_aware_datetime(" ")


@pytest.mark.cmd
@pytest.mark.django_db
def test_cmd_contributors(capfd, dummy_contributors,
                          default_contributors_kwargs, contributors_kwargs):
    """Contributors across the site."""
    result_kwargs = default_contributors_kwargs.copy()
    result_kwargs.update(contributors_kwargs)
    cmd_args = []
    for k in ["project", "language"]:
        if result_kwargs["%s_codes" % k]:
            for arg in result_kwargs["%s_codes" % k]:
                cmd_args.extend(["--%s" % k, arg])
    for k in ["since", "until"]:
        if result_kwargs[k]:
            cmd_args.extend(
                ["--%s" % k,
                 result_kwargs[k]])
            result_kwargs[k] = make_aware(parse_datetime(result_kwargs[k]))

    if result_kwargs["sort_by"]:
        cmd_args.extend(["--sort-by", result_kwargs["sort_by"]])

    call_command('contributors', *cmd_args)
    out, err = capfd.readouterr()
    assert out.strip() == str(
        "\n".join(
            "%s (%s contributions)" % (k, v)
            for k, v
            in result_kwargs.items()))


@pytest.mark.cmd
def test_cmd_contributors_mutually_exclusive(capfd):
    """Test mutually exclusive arguments are not accepted."""
    with pytest.raises(CommandError) as e:
        call_command('contributors', '--include-anonymous', '--mailmerge')
    assert ("argument --mailmerge: not allowed with argument "
            "--include-anonymous") in str(e)

    with pytest.raises(CommandError) as e:
        call_command('contributors', '--mailmerge', '--include-anonymous')
    assert ("argument --include-anonymous: not allowed with argument "
            "--mailmerge") in str(e)


@pytest.mark.cmd
@pytest.mark.django_db
def test_cmd_contributors_mailmerge(capfd, dummy_email_contributors):
    """Contributors across the site with mailmerge."""
    call_command('contributors', '--mailmerge')
    out, err = capfd.readouterr()
    temp = OrderedDict(sorted(CONTRIBUTORS_WITH_EMAIL.items(),
                              key=lambda x: str.lower(x[1]['username'])))
    expected = [
        formataddr((item["full_name"].strip() or item["username"],
                    item['email'].strip()))
        for item in temp.values() if item['email'].strip()]
    assert out.strip() == "\n".join(expected)
