# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest


@pytest.fixture
def command_caller():

    def call_command_object(command, *args, **options):
        parser = command.create_parser('', command.name)
        opt_mapping = {
            sorted(o.option_strings)[0].lstrip('-').replace('-', '_'): o.dest
            for o in parser._actions if o.option_strings}
        arg_options = {
            opt_mapping.get(key, key): value for key, value in options.items()}
        defaults = parser.parse_args(args=args)
        defaults = dict(defaults._get_kwargs(), **arg_options)
        args = defaults.pop('args', ())
        return command.execute(*args, **defaults)

    def _call_command(command, *args):
        exited = False
        try:
            call_command_object(command, *args)
        except SystemExit:
            exited = True
            return exited
    return _call_command


@pytest.fixture
def argv_caller():

    def _call_argv(command, *args):
        exited = False
        try:
            command.run_from_argv((["", "foo"] + list(args)))
        except SystemExit:
            exited = True
        return exited
    return _call_argv


@pytest.fixture(params=["command", "argv"])
def command_calls(request, argv_caller, command_caller):
    if request.param == "command":
        return command_caller
    return argv_caller
