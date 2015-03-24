#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

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
