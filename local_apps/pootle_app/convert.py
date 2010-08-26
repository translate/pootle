#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009 Zuza Software Foundation
#
# This file is part of translate.
#
# translate is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# translate is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with translate; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

from translate.convert import xliff2po, po2xliff, po2ts, xliff2oo, po2oo

convert_table = {
    ('po', 'oo'):  po2oo.convertoo,
    ('po', 'ts'):  po2ts.convertpo,
    ('po', 'xlf'): po2xliff.convertpo,
    ('xlf', 'oo'): xliff2oo.convertoo,
    ('xlf', 'po'): xliff2po.convertxliff,
}
