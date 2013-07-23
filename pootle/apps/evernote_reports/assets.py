#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2013 Evernote Corporation
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


js_reports = Bundle(
    'js/jquery/jquery.history.js',
    'js/jquery/jquery.tmpl.js',
    'js/evernote/kalendae.js',
    'js/evernote/reports.js',
    filters='rjsmin', output='js/evernote/reports.min.js')
register('js_evernote_reports', js_reports)

css_reports = Bundle(
    'css/evernote/reports.css',
    'css/evernote/kalendae.css',
    filters='cssmin', output='css/evernote/reports.min.css')
register('css_evernote_reports', css_reports)
