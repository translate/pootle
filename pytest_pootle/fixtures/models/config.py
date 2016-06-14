# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from collections import OrderedDict

import pytest


BAD_CONFIG_FLAGS = OrderedDict(
    [("get_and_set",
      ("-s", "foo", "bar", "-g", "foo")),
     ("get_and_append",
      ("-a", "foo", "bar", "-g")),
     ("get_and_list",
      ("-l", "-g")),
     ("get_and_clear",
      ("-c", "foo", "-g")),
     ("list_and_set",
      ("-s", "foo", "bar", "-l")),
     ("list_and_append",
      ("-a", "foo", "bar", "-l")),
     ("list_and_clear",
      ("-c", "foo", "-l")),
     ("set_and_append",
      ("-a", "foo", "bar", "-s", "foo2", "bar2")),
     ("set_and_clear",
      ("-c", "foo", "-s", "foo2", "bar2")),
     ("bad_ct", "foobar"),
     ("missing_ct", "foo.bar")])


@pytest.fixture(params=BAD_CONFIG_FLAGS.keys())
def bad_config_flags(request):
    return BAD_CONFIG_FLAGS[request.param]


@pytest.fixture
def no_config_env():
    from pootle_config.models import Config
    Config.objects.all().delete()
