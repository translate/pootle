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

from django_assets import Bundle, register

js_common = Bundle(
    'js/jquery/jquery.js', 'js/jquery/jquery.tipsy.js',
    'js/jquery/jquery.cookie.js', 'js/jquery/jquery.bidi.js',
    'js/jquery/jquery.fancybox.js', 'js/jquery/jquery.utils.js',
    'js/jquery/jquery.easing.js', 'js/jquery/jquery.serializeObject.js',
    'js/bootstrap/bootstrap-alert.js', 'js/bootstrap/bootstrap-transition.js',
    'js/common.js', 'js/search.js', 'js/sorttable.js', 'js/spin.js',
    'js/utils.js', 'js/shortcut.js',  # Leave shortcut.js as the last one
    filters='rjsmin', output='js/common.min.js')
register('js_common', js_common)

js_admin = Bundle(
    'js/admin.js',
    filters='rjsmin', output='js/admin.min.js')
register('js_admin', js_admin)

js_editor = Bundle(
    'js/jquery/jquery.history.js', 'js/jquery/jquery.tmpl.js',
    'js/jquery/jquery.textarea-expander.js', 'js/diff_match_patch.js',
    'js/jquery/jquery.fieldselection.js', 'js/jquery/jquery.caret.js',
    'js/jquery/jquery.highlightRegex.js', 'js/jquery/jquery.jsonp.js',
    'js/editor.js', 'js/json2.js',
    filters='rjsmin', output='js/editor.min.js')
register('js_editor', js_editor)

css_common = Bundle(
    'css/style.css', 'css/fancybox.css', 'css/tipsy.css',
    'css/markup.css', 'css/sprite.css',
    filters='cssmin', output='css/common.min.css')
register('css_common', css_common)

css_admin = Bundle(
    'css/admin.css',
    filters='cssmin', output='css/admin.min.css')
register('css_admin', css_admin)

css_editor = Bundle(
    'css/editor.css',
    filters='cssmin', output='css/editor.min.css')
register('css_editor', css_editor)

css_custom = Bundle(
    'css/custom/custom.css',
    filters='cssmin', output='css/custom/custom.min.css')
register('css_custom', css_custom)
