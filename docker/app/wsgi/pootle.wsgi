#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import os

from django.core.wsgi import get_wsgi_application


os.environ['DJANGO_SETTINGS_MODULE'] = 'pootle.settings'
os.environ['POOTLE_SETTINGS'] = '/app/pootle.conf'

# import newrelic.agent
# NEW_RELIC_CONFIG = os.path.join(os.path.dirname(__file__), "newrelic.ini")

# print "LOADING NEWRELIC..."
# print "from %s" % NEW_RELIC_CONFIG
# print newrelic.agent.initialize(NEW_RELIC_CONFIG)

application = get_wsgi_application()
