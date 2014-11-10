#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2012-2013 Zuza Software Foundation
# Copyright 2013-2014 Evernote Corporation
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


# <Webpack>
# These are handled by webpack and therefore have no filters applied
# They're kept here so hash-based cache invalidation can be used

js_vendor = Bundle(
    'js/vendor.bundle.js',
    output='js/vendor.min.%(version)s.js')
register('js_vendor', js_vendor)

js_common = Bundle(
    'js/common/app.bundle.js',
    output='js/common/app.min.%(version)s.js')
register('js_common', js_common)

js_admin_general_app = Bundle(
    'js/admin/general/app.bundle.js',
    output='js/admin/general/app.min.%(version)s.js')
register('js_admin_general_app', js_admin_general_app)

js_admin_users_app = Bundle(
    'js/admin/users/app.bundle.js',
    output='js/admin/users/app.min.%(version)s.js')
register('js_admin_users_app', js_admin_users_app)

js_user_app = Bundle(
    'js/user/app.bundle.js',
    output='js/user/app.min.%(version)s.js')
register('js_user_app', js_user_app)

js_editor = Bundle(
    'js/editor/app.bundle.js',
    output='js/editor/app.min.%(version)s.js')
register('js_editor', js_editor)

js_reports = Bundle(
    'js/reports/app.bundle.js',
    filters='rjsmin', output='js/reports.min.js')
register('js_reports', js_reports)

# </Webpack>


css_reports = Bundle(
    'css/reports.css',
    filters='cssmin', output='css/reports.min.css')
register('css_reports', css_reports)

css_common = Bundle(
    'css/style.css',
    'css/actions.css',
    'css/buttons.css',
    'css/contact.css',
    'css/error.css',
    'css/login.css',
    'css/magnific-popup.css',
    'css/navbar.css',
    'css/odometer.css',
    'css/popup.css',
    'css/tipsy.css',
    'css/sprite.css',
    'css/select2.css',
    'css/select2-pootle.css',
    'css/scores.css',
    'css/user.css',
    'css/welcome.css',
    filters='cssmin', output='css/common.min.%(version)s.css')
register('css_common', css_common)

css_admin = Bundle(
    'css/admin.css',
    filters='cssmin', output='css/admin.min.%(version)s.css')
register('css_admin', css_admin)

css_editor = Bundle(
    'css/editor.css',
    filters='cssmin', output='css/editor.min.%(version)s.css')
register('css_editor', css_editor)
