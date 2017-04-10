# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from __future__ import absolute_import

import json

from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.utils.encoding import force_text
from django.utils.functional import Promise

from ..markup import Markup


class PootleJSONEncoder(DjangoJSONEncoder):
    """Custom JSON encoder for Pootle.

    This is mostly implemented to avoid calling `force_text` all the time on
    certain types of objects.
    https://docs.djangoproject.com/en/1.10/topics/serialization/#djangojsonencoder
    """

    def default(self, obj):
        if isinstance(obj, (Promise, Markup)):
            return force_text(obj)

        return super(PootleJSONEncoder, self).default(obj)


def jsonify(obj):
    """Serialize Python `obj` object into a JSON string."""
    if settings.DEBUG:
        indent = 4
    else:
        indent = None

    return json.dumps(obj, indent=indent, cls=PootleJSONEncoder)
