# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.


def view_context_test(ctx, **assertions):
    for k, v in assertions.items():
        if k == "check_categories":
            for i, cat in enumerate(ctx[k]):
                assert v[i] == cat
        elif k == "checks" and ctx["page"] == "translate":
            for _k, _v in ctx[k].items():
                for i, check in enumerate(v[_k]["checks"]):
                    for __k, __v in check.items():
                        assert _v["checks"][i][__k] == __v
        elif k in ["translation_states", "checks"] and ctx["page"] == "browse":
            for i, cat in enumerate(ctx[k]):
                for _k, _v in cat.items():
                    assert str(ctx[k][i][_k]) == str(_v)
        elif k == "search_form":
            assert ctx[k].as_p() == v.as_p()
        elif k == "table":
            for tk in ["id", "fields", "headings"]:
                assert ctx[k][tk] == v[tk]
            assert list(ctx[k]["rows"]) == list(v["rows"])
        else:
            assert ctx[k] == v
