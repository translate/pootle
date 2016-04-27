# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.http import HttpResponse

from .utils.json import jsonify


class JsonResponse(HttpResponse):
    """An HTTP response class that consumes data to be serialized to JSON.

    :param data: Data to be dumped into json.
    """

    def __init__(self, data, **kwargs):
        kwargs.setdefault('content_type', 'application/json')
        data = jsonify(data)
        super(JsonResponse, self).__init__(content=data, **kwargs)


class JsonResponseBadRequest(JsonResponse):
    status_code = 400


class JsonResponseForbidden(JsonResponse):
    status_code = 403


class JsonResponseNotFound(JsonResponse):
    status_code = 404


class JsonResponseServerError(JsonResponse):
    status_code = 500
