#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import os
import sys

from django.core.management import execute_from_command_line

from pootle import syspath_override  # noqa


if __name__ == "__main__":
    from pootle.core.log import cmd_log
    cmd_log(*sys.argv)
    os.environ['DJANGO_SETTINGS_MODULE'] = 'pootle.settings'
    execute_from_command_line()
