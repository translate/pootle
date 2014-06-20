#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2014 Evernote Corporation
#
# This file is part of Pootle.
#
# Pootle is free software; you can redistribute it and/or modify
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

try:
    from elasticsearch import Elasticsearch as ES
except:
    ES = None

from django.conf import settings


def get_tmserver_params():
    params = getattr(settings, 'POOTLE_TM_SERVER', None)

    if params is not None:
        return params['default']

    return None


es_params = get_tmserver_params()
# TODO support ENGINE param
# Elasticsearch is the only supported engine now
es = None
if ( es_params is not None and ES is not None ):
    es = ES([{'host': es_params['HOST'], 'port': es_params['PORT']}, ])


def update_tmserver(language, obj):
    if es is not None:
        es.index(index=es_params['INDEX_NAME'],
                 doc_type=language,
                 body=obj,
                 id=obj['id'])
