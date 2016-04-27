# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import importlib
import logging

from . import SearchBackend


class SearchBroker(SearchBackend):
    def __init__(self, config_name=None):
        super(SearchBroker, self).__init__(config_name)
        self._servers = {}

        if self._settings is None:
            return

        for server in self._settings:
            if config_name is None or server in config_name:
                try:
                    _module = '.'.join(
                        self._settings[server]['ENGINE'].split('.')[:-1])
                    _search_class = \
                        self._settings[server]['ENGINE'].split('.')[-1]
                except KeyError:
                    logging.warning("Search engine '%s' is missing the "
                                    "required 'ENGINE' setting", server)
                    break
                try:
                    module = importlib.import_module(_module)
                    try:
                        self._servers[server] = getattr(module,
                                                        _search_class)(server)
                    except AttributeError:
                        logging.warning("Search backend '%s'. No search class "
                                        "'%s' defined.", server, _search_class)
                except ImportError:
                    logging.warning("Search backend '%s'. Cannot import '%s'",
                                    server, _module)

    def search(self, unit):
        if not self._servers:
            return []

        results = []
        counter = {}
        for server in self._servers:
            for result in self._servers[server].search(unit):
                translation_pair = result['source'] + result['target']
                if translation_pair not in counter:
                    counter[translation_pair] = result['count']
                    results.append(result)
                else:
                    counter[translation_pair] += result['count']

        for item in results:
            item['count'] = counter[item['source']+item['target']]

        # Results are in the order of the TM servers, so they must be sorted by
        # score so the better matches are presented to the user.
        results = sorted(results, reverse=True,
                         key=lambda item: item['score'])

        return results

    def update(self, language, obj):
        for server in self._servers:
            if self._servers[server].is_auto_updatable:
                self._servers[server].update(language, obj)
