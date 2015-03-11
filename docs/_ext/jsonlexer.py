#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2012 Zuza Software Foundation
#
# This file is part of Pootle.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.

"""Sphinx extension to enable JSON code highlighting."""


def setup(app):
    # enable Pygments json lexer
    try:
        import pygments
        if pygments.__version__ >= '1.5':
            # use JSON lexer included in recent versions of Pygments
            from pygments.lexers import JsonLexer
        else:
            # use JSON lexer from pygments-json if installed
            from pygson.json_lexer import JSONLexer as JsonLexer
    except ImportError:
        pass  # not fatal if we have old (or no) Pygments and no pygments-json
    else:
        app.add_lexer('json', JsonLexer())

    return {"parallel_read_safe": True}
