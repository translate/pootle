#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009 Mozilla Corporation
# Copyright 2009, 2013 Zuza Software Foundation
#
# This file is part of Pootle.
#
# Pootle is free software; you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# Pootle is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# Pootle; if not, see <http://www.gnu.org/licenses/>.

import logging

import ldap
import ldap.filter  # It is necessary to explicitly import ldap.filter.

from django.conf import settings
from django.contrib.auth import get_user_model


User = get_user_model()


class LdapBackend(object):
    """Django authentication module which implements LDAP authentication.

    To use this module, simply add it to the tuple AUTHENTICATION_BACKENDS in
    settings.py.
    """
    def authenticate(self, username=None, password=None):

        logger = logging.getLogger('pootle.auth.ldap')

        ldo = ldap.initialize(settings.AUTH_LDAP_SERVER)
        ldo.set_option(ldap.OPT_PROTOCOL_VERSION, 3)

        try:
            ldo.simple_bind_s(settings.AUTH_LDAP_ANON_DN,
                              settings.AUTH_LDAP_ANON_PASS)

            result = ldo.search_s(
                settings.AUTH_LDAP_BASE_DN,
                ldap.SCOPE_SUBTREE,
                (settings.AUTH_LDAP_FILTER %
                 ldap.filter.escape_filter_chars(username)),
                settings.AUTH_LDAP_FIELDS.values()
            )

            if len(result) != 1:
                logger.debug("More or less than 1 matching account for (%s).  "
                             "Failing LDAP auth." % username)
                return None

        except ldap.INVALID_CREDENTIALS:
            logger.exception('Anonymous bind to LDAP server failed. Please '
                             'check the username and password.')
            return None
        except Exception as e:
            logger.exception('Unknown LDAP error: ' + str(e))
            return None

        try:
            ldo.simple_bind_s(result[0][0], password)
            logger.debug("Successful LDAP login for user (%s)" % (username))

            try:
                user = User.objects.get(username=username)
                return user
            except User.DoesNotExist:
                logger.info("First login for LDAP user (%s). Creating new "
                            "account." % username)
                user = User(username=username, is_active=True)
                user.set_unusable_password()
                for i in settings.AUTH_LDAP_FIELDS:
                    if i != 'dn' and len(settings.AUTH_LDAP_FIELDS[i]) > 0:
                        setattr(user, i,
                                result[0][1][settings.AUTH_LDAP_FIELDS[i]][0])
                user.save()
                return user

        # Bad e-mail or password.
        except (ldap.INVALID_CREDENTIALS, ldap.UNWILLING_TO_PERFORM):
            logger.debug("No account or bad credentials for (%s). Failing "
                         "LDAP auth." % username)
            return None
        except Exception as e:  # No other exceptions are normal.
            logger.exception('Unknown LDAP error: ' + str(e))
            raise

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
