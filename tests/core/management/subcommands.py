#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from collections import OrderedDict

from django.core import management
from django.core.management.base import CommandError, SystemCheckError

from pootle.core.delegate import subcommands
from pootle.core.plugin import provider
from pootle.core.management.subcommands import CommandWithSubcommands


@pytest.mark.django_db
def test_command_with_subcommands_instance(capsys, command_caller):

    class FooCommand(CommandWithSubcommands):

        name = "foo"
        help = "Do a foo"

        def handle(self, *args, **options):
            self.stdout.write("Did a foo")

    foo_command = FooCommand()
    assert not foo_command.subcommands
    command_caller(foo_command)
    out, err = capsys.readouterr()
    assert out == u'Did a foo\n'


def test_command_with_subcommands_help(capsys, command_calls):

    class FooCommand(CommandWithSubcommands):

        name = "foo"
        help = "Do a foo"

    foo_command = FooCommand()
    exited = command_calls(foo_command, "--help")
    assert exited
    out, err = capsys.readouterr()
    assert u'Do a foo' in out
    assert "subcommands" not in out.lower()


@pytest.mark.django_db
def test_command_with_subcommands_sub(capsys, command_calls):

    class FooCommand(CommandWithSubcommands):

        name = "foo"
        help = "Do a foo with subcommands"

    class BarSubcommand(management.BaseCommand):
        pass

    @provider(subcommands, sender=FooCommand)
    def provide_subcommands(**kwargs):
        return dict(bar=BarSubcommand)

    foo_command = FooCommand()
    assert foo_command.subcommands["bar"] == BarSubcommand
    command_calls(foo_command)
    out, err = capsys.readouterr()
    assert (
        out
        == (u'Do a foo with subcommands\nAvailable subcommands'
            u'\n=====================\n\nbar\n'))
    exited = command_calls(foo_command, "--help")
    assert exited
    out, err = capsys.readouterr()
    assert "subcommands" in out.lower()
    assert "{bar}" in out


def test_command_with_subcommands_many_subs(capsys, command_calls):

    class FooCommand(CommandWithSubcommands):

        name = "foo"
        help = "Do a foo with subcommands"

    class BarSubcommand(management.BaseCommand):

        @property
        def help(self):
            return "Do a bar for a foo"

    @provider(subcommands, sender=FooCommand)
    def provide_subcommands(**kwargs):
        return OrderedDict(
            [("bar1", BarSubcommand),
             ("bar2", BarSubcommand),
             ("bar3", BarSubcommand)])

    @provider(subcommands, sender=FooCommand)
    def provide_more_subcommands(**kwargs):
        return OrderedDict(
            [("bar4", BarSubcommand),
             ("bar5", BarSubcommand),
             ("bar6", BarSubcommand)])

    foo_command = FooCommand()
    assert foo_command.subcommands.keys() == [
        "bar1", "bar2", "bar3", "bar4", "bar5", "bar6"]
    exited = command_calls(foo_command, "--help")
    assert exited
    out, err = capsys.readouterr()
    assert "subcommands" in out.lower()
    for k in foo_command.subcommands.keys():
        assert k in out
        assert "Do a bar for a foo" in out


@pytest.mark.django_db
def test_command_with_subcommands_sub_call(capsys, command_calls):

    class FooCommand(CommandWithSubcommands):

        name = "foo"

    class BarSubcommand(management.BaseCommand):

        name = "bar"

        def handle(self, *args, **options):
            self.stdout.write("Bar subcommand called")

    @provider(subcommands, sender=FooCommand)
    def provide_subcommands(**kwargs):
        return dict(bar=BarSubcommand)

    foo_command = FooCommand()
    command_calls(foo_command, "bar")
    out, err = capsys.readouterr()
    assert out == "Bar subcommand called\n"
    exited = command_calls(foo_command, "bar", "--help")
    assert exited
    out, err = capsys.readouterr()
    assert "usage: foo bar" in out


@pytest.mark.django_db
def test_command_with_subcommands_sub_args(capsys, command_calls):

    class FooCommand(CommandWithSubcommands):

        name = "foo"

    class BarSubcommand(management.BaseCommand):

        msg_called = "Bar called by %s with the subcommand %s"

        def add_arguments(self, parser):
            super(BarSubcommand, self).add_arguments(parser)
            parser.add_argument(
                '--fooarg',
                type=str,
                help='Help with foo arg')

        def handle(self, *args, **options):
            self.stdout.write(
                "Bar called with fooarg: %s" % options["fooarg"])

    @provider(subcommands, sender=FooCommand)
    def provide_subcommands(**kwargs):
        return dict(bar=BarSubcommand)

    foo_command = FooCommand()
    command_calls(foo_command, "bar", "--fooarg", "BAR")
    out, err = capsys.readouterr()
    assert out == "Bar called with fooarg: BAR\n"


def test_command_with_subcommands_bad_args(capsys):

    class FooCommand(CommandWithSubcommands):
        pass

    foo_command = FooCommand()
    with pytest.raises(SystemExit):
        foo_command.run_from_argv(["", "foo", "bad", "args"])
    out, err = capsys.readouterr()
    assert err.startswith("usage:  foo")
    assert "unrecognized arguments: bad args" in err


def test_command_with_subcommands_bad_exec(capsys):

    class RandomError(Exception):
        pass

    class FooCommand(CommandWithSubcommands):

        def execute(self, *args, **options):
            raise RandomError("OOPS")

    foo_command = FooCommand()
    with pytest.raises(RandomError):
        foo_command.run_from_argv(["", "foo"])


def test_command_with_subcommands_bad_syscheck(capsys):

    class FooCommand(CommandWithSubcommands):

        def execute(self, *args, **options):
            raise SystemCheckError("BAD SYSTEM")

    foo_command = FooCommand()
    with pytest.raises(SystemExit):
        foo_command.run_from_argv(["", "foo"])
    out, err = capsys.readouterr()
    assert err == "BAD SYSTEM\n"


def test_command_with_subcommands_bad_commanderror(capsys):

    class FooCommand(CommandWithSubcommands):

        def execute(self, *args, **options):
            raise CommandError("BAD COMMAND")

    foo_command = FooCommand()
    with pytest.raises(SystemExit):
        foo_command.run_from_argv(["", "foo"])
    out, err = capsys.readouterr()
    assert err == u'CommandError: BAD COMMAND\n'
