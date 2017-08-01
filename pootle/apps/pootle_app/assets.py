# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import os

from django_assets import Bundle, register

from django.conf import settings


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

js_fs_app = Bundle(
    'js/fs/app.bundle.js',
    output='js/fs/app.min.%(version)s.js')
register('js_fs_app', js_fs_app)


js_user_app = Bundle(
    'js/user/app.bundle.js',
    output='js/user/app.min.%(version)s.js')
register('js_user_app', js_user_app)

js_editor = Bundle(
    'js/editor/app.bundle.js',
    output='js/editor/app.min.%(version)s.js')
register('js_editor', js_editor)


rel_path = os.path.join('js', 'select2_l10n')
select2_l10n_dir = os.path.join(settings.WORKING_DIR, 'static', rel_path)
l10n_files = [os.path.join(rel_path, f)
              for f in os.listdir(select2_l10n_dir)
              if (os.path.isfile(os.path.join(select2_l10n_dir, f))
                  and f.endswith('.js'))]
for l10n_file in l10n_files:
    lang = l10n_file.split(os.sep)[-1].split('.')[-2]
    register('select2-l10n-%s' % lang,
             Bundle(l10n_file,
                    output='js/select2-l10n-' + lang + '.min.%(version)s.js'))


# </Webpack>

css_common = Bundle(
    'css/style.css',
    'css/actions.css',
    'css/breadcrumbs.css',
    'css/buttons.css',
    'css/contact.css',
    'css/error.css',
    'css/auth.css',
    'css/magnific-popup.css',
    'css/navbar.css',
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
