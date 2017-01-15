# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import os
import sys
from collections import OrderedDict

from django.core.management import (
    BaseCommand, CommandError, CommandParser, handle_default_options)
from django.core.management.base import SystemCheckError
from django.db import connections
from django.utils.functional import cached_property

from pootle.core.delegate import subcommands


class SubcommandsError(CommandError):

    pass


class SubcommandsParser(CommandParser):

    def parse_args(self, args):
        try:
            # first find if we have a known subcommand
            known, __ = self.parse_known_args(args)
        except SubcommandsError:
            known = None
        is_subcommand = (
            known
            and hasattr(known, "subcommand")
            and known.subcommand in self.cmd.subcommands)
        if is_subcommand:
            # if there is a subcommand then move it in argv to the front of other
            # params and defer to the the subcommand
            args = list(args)
            del args[args.index(known.subcommand)]
            parser = self.cmd.subcommands[
                known.subcommand]().create_parser(self.prog, known.subcommand)
            options = parser.parse_args(tuple(args))
            options.subcommand = known.subcommand
            return options
        else:
            # otherwise make subcommand optional
            for action in self._actions:
                if action.dest == "subcommand":
                    action.option_strings = [""]
        return super(SubcommandsParser, self).parse_args(args)

    def error(self, message):
        raise SubcommandsError(message)


class SubcommandsSubParser(CommandParser):

    def format_help(self):
        parent = self.cmd.create_parser("", "")
        formatter = self._get_formatter()

        # usage - include options from parent
        parent_actions = [x for x in parent._actions if x.dest != "subcommand"]
        formatter.add_usage(self.usage, parent_actions + self._actions,
                            self._mutually_exclusive_groups)

        # description
        formatter.add_text(self.description)

        sub_actions = set(["subcommand"])
        for action_group in self._action_groups:
            for group_action in action_group._group_actions:
                sub_actions.add(group_action.dest)

        # positionals, optionals and user-defined groups for parent
        for action_group in parent._action_groups:
            # dont include the subcommands from parent
            group_actions = [
                group_action
                for group_action
                in action_group._group_actions
                if group_action.dest not in sub_actions]
            if group_actions:
                formatter.start_section(action_group.title)
                formatter.add_text(action_group.description)
                formatter.add_arguments(group_actions)
                formatter.end_section()

        # positionals, optionals and user-defined groups for subcommand
        for action_group in self._action_groups:
            formatter.start_section(
                "%s for the *%s* subcommand"
                % (action_group.title, self.prog.split(" ")[-1]))
            formatter.add_text(action_group.description)
            group_actions = action_group._group_actions
            if group_actions and group_actions[0].dest == "help":
                group_actions = group_actions[1:]
            formatter.add_arguments(group_actions)
            formatter.end_section()

        # epilog
        formatter.add_text(self.epilog)

        # determine help from format above
        return formatter.format_help()


class CommandWithSubcommands(BaseCommand):

    @cached_property
    def subcommands(self):
        return OrderedDict(subcommands.gather(self.__class__))

    def handle(self, *args, **kwargs):
        self.stdout.write(self.help)
        if self.subcommands:
            title = "Available subcommands"
            self.stdout.write(title)
            self.stdout.write("=" * len(title))
            self.stdout.write("")
            subs = "\n".join(self.subcommands.keys())
            self.stdout.write(subs)

    def handle_exception(self, e, options=None):
        do_raise = (
            (options and options.traceback)
            or not isinstance(e, CommandError))
        if do_raise:
            raise e
        if isinstance(e, SystemCheckError):
            self.stderr.write(str(e), lambda x: x)
        else:
            self.stderr.write('%s: %s' % (e.__class__.__name__, e))
        sys.exit(1)

    def run_from_argv(self, argv):
        """
        Override django's run_from_argv to parse a subcommand.
        If the subcommand is present, then mangle argv and defer to the
        subcommand
        """
        self._called_from_command_line = True
        parser = self.create_parser(argv[0], argv[1])
        try:
            # first find if we have a known subcommand
            known, __ = parser.parse_known_args(argv[2:])
        except SubcommandsError:
            known = None
        except Exception as e:
            self.handle_exception(e)
        is_subcommand = (
            known
            and hasattr(known, "subcommand")
            and known.subcommand in self.subcommands)
        if is_subcommand:
            # if there is a subcommand then move it in argv to the front of other
            # params and defer to the the subcommand
            del argv[argv.index(known.subcommand)]
            argv[1] = "%s %s" % (argv[1], known.subcommand)
            return self.subcommands[known.subcommand]().run_from_argv(argv)
        # continue with the normal parsing/execution
        # and make subcommand optional
        for action in parser._actions:
            if action.dest == "subcommand":
                action.option_strings = [""]
        try:
            options = parser.parse_args(argv[2:])
        except SubcommandsError as e:
            # we have to raise SystemExit here if necessary
            parser.print_usage(sys.stderr)
            return parser.exit(2, "%s\n" % e)
        cmd_options = vars(options)
        args = cmd_options.pop('args', ())
        handle_default_options(options)
        try:
            self.execute(*args, **cmd_options)
        except Exception as e:
            self.handle_exception(e, options)
        finally:
            connections.close_all()

    def add_arguments(self, parser):
        if not self.subcommands:
            return
        subparsers = parser.add_subparsers(
            title="subcommands",
            dest="subcommand",
            parser_class=SubcommandsSubParser)
        for name, subcommand in self.subcommands.items():
            subc = subcommand()
            kwargs = dict(cmd=subc)
            for k in ("help", "description"):
                v = getattr(subc, k, None)
                if v:
                    kwargs[k] = v
            subparser = subparsers.add_parser(name, **kwargs)
            subc.add_arguments(subparser)

    def add_default_arguments(self, parser):
        parser.add_argument(
            '--version', action='version', version=self.get_version())
        parser.add_argument(
            '-v', '--verbosity', action='store', dest='verbosity', default='1',
            type=int, choices=[0, 1, 2, 3],
            help=(
                'Verbosity level; 0=minimal output, 1=normal output, '
                '2=verbose output, 3=very verbose output'))
        parser.add_argument(
            '--settings',
            help=(
                'The Python path to a settings module, e.g. '
                '"myproject.settings.main". If this isn\'t provided, the '
                'DJANGO_SETTINGS_MODULE environment variable will be used.'))
        parser.add_argument(
            '--pythonpath',
            help=(
                'A directory to add to the Python path, '
                'e.g. "/home/djangoprojects/myproject".'))
        parser.add_argument(
            '--traceback', action='store_true',
            help='Raise on CommandError exceptions')
        parser.add_argument(
            '--no-color', action='store_true', dest='no_color', default=False,
            help="Don't colorize the command output.")

    def create_parser(self, prog_name, subcommand):
        parser = SubcommandsParser(
            self,
            prog=(
                "%s %s"
                % (os.path.basename(prog_name),
                   subcommand)),
            description=self.help or None)
        self.add_default_arguments(parser)
        self.add_arguments(parser)
        return parser

    def execute(self, *args, **options):
        sub = options.pop("subcommand", None)
        if sub:
            return self.subcommands[sub]().execute(*args, **options)
        return super(CommandWithSubcommands, self).execute(*args, **options)
