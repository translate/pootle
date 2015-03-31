#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

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

js_admin_app = Bundle(
    'js/admin/app.bundle.js',
    output='js/admin/app.min.%(version)s.js')
register('js_admin_app', js_admin_app)

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
    'css/auth.css',
    'css/magnific-popup.css',
    'css/navbar.css',
    'css/odometer.css',
    'css/popup.css',
    'css/react-select.css',
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
