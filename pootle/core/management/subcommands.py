# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from collections import OrderedDict

from django.utils.functional import cached_property

from dj import subcommand

from pootle.core.delegate import subcommands


class CommandWithSubcommands(subcommand.CommandWithSubcommands):

    @cached_property
    def subcommands(self):
        return OrderedDict(subcommands.gather(self.__class__))
