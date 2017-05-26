# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import logging

from django.conf import settings
from django.http import JsonResponse

from allauth.account.adapter import DefaultAccountAdapter

from pootle.i18n.gettext import ugettext_lazy as _


logger = logging.getLogger('action')


class PootleAccountAdapter(DefaultAccountAdapter):
    """Reimplementation of DefaultAccountAdapter from allauth to change
    ajax_response and username validation.

    Differences:
      - the html key is removed for performance reasons
      - form_errors is renamed to errors
      - Latin1 usernames are allowed
    """

    def ajax_response(self, request, response, form=None, data=None,
                      redirect_to=None):
        if data is None:
            data = {}
        if redirect_to:
            status = 200
            data["location"] = redirect_to

        if form:
            if form.is_valid():
                status = 200
            else:
                status = 400
                data["errors"] = form._errors

        return JsonResponse(data, status=status)

    def is_open_for_signup(self, request):
        """Controls whether signups are enabled on the site.

        This can be changed by setting `POOTLE_SIGNUP_ENABLED = False` in
        the settings. Defaults to `True`.
        """
        return getattr(settings, 'POOTLE_SIGNUP_ENABLED', True)

    def add_message(self, request, level, message_template, *args, **kwargs):
        """Silence messages altogether."""
        pass

    def send_confirmation_mail(self, *args, **kwargs):
        try:
            super(PootleAccountAdapter, self).send_confirmation_mail(*args,
                                                                     **kwargs)
        except Exception:
            logger.exception("ERROR: Sign up failed. Couldn't sent "
                             "confirmation email.")
            raise RuntimeError(_('Some problem happened when tried to send '
                                 'the confirmation email. Please try again '
                                 'later.'))
