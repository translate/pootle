# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.


class UnitTextSearch(object):
    """Search Unit's fields for text strings
    """

    search_fields = (
        "source_f", "target_f", "locations",
        "translator_comment", "developer_comment")
    search_mappings = {
        "notes": ["translator_comment", "developer_comment"],
        "source": ["source_f"],
        "target": ["target_f"]}

    def __init__(self, qs):
        self.qs = qs

    def get_search_fields(self, sfields):
        search_fields = set()
        for field in sfields:
            if field in self.search_mappings:
                search_fields.update(self.search_mappings[field])
            elif field in search_fields:
                search_fields.add(field)
        return search_fields

    def get_words(self, text, exact):
        if exact:
            return [text]
        return [t.strip() for t in text.split(" ") if t.strip()]

    def search(self, text, sfields, exact=False):
        result = self.qs.none()
        words = self.get_words(text, exact)

        for k in self.get_search_fields(sfields):
            result = result | self.search_field(k, words)
        return result

    def search_field(self, k, words):
        subresult = self.qs
        for word in words:
            subresult = subresult.filter(
                **{("%s__icontains" % k): word})
        return subresult
