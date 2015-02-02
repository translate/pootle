#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.http import JsonResponse

from allauth.account.adapter import DefaultAccountAdapter


class PootleAccountAdapter(DefaultAccountAdapter):
    """Reimplementation of DefaultAccountAdapter from allauth to change
    ajax_response.

    Differences:
      - the html key is removed for performance reasons
      - form_errors is renamed to errors
    """
    def ajax_response(self, request, response, redirect_to=None, form=None):
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
