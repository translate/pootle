# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from pootle.i18n.gettext import ugettext_lazy as _


FS_PRESETS = (
    ("/po/<language_code>.<ext>", _("GNU style")),
    ("/<language_code>/<dir_path>/<filename>.<ext>", _("non-GNU style")),
    ("/locale/<language_code>/LC_MESSAGES/<filename>.<ext>", _("Django style")),
    ("", _("Custom")))
