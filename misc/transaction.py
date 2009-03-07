#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008 Zuza Software Foundation
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

from django.db import transaction

def django_transaction(f):
    def decorated_f(*args, **kwargs):
        result = None
        try:
            try:
                transaction.enter_transaction_management()
                transaction.managed(True)

                return f(*args, **kwargs)
            except:
                if transaction.is_dirty():
                    transaction.rollback()
                transaction.leave_transaction_management()
                raise
        finally:
            if transaction.is_managed():
                if transaction.is_dirty():
                    transaction.commit()
            transaction.leave_transaction_management()
    return decorated_f
