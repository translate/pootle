# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from datetime import timedelta
from itertools import groupby

from django.utils import timezone

from pootle.core.delegate import event_formatters, log, profile
from pootle.core.views.panels import Panel
from pootle_log.utils import ComparableLogEvent


class StoreActivityPanel(Panel):
    template_name = "browser/includes/store_activity.html"
    panel_name = "store-activity"

    def get_context_data(self):
        ctx = {}
        formatters = event_formatters.gather(self.view.object.__class__)
        ctx["contributors"] = set()
        start = timezone.now() - timedelta(days=30)
        # start = None
        event_log = log.get(self.view.object.__class__)(self.view.object)
        events = groupby(
            sorted(
                ComparableLogEvent(ev)
                for ev
                in event_log.get_events(start=start)),
            lambda event: (
                event.timestamp and event.timestamp.replace(second=0),
                (event.value.user
                 if event.action == "suggestion_accepted"
                 else event.user)))
        _events = []
        for timestamp, evts in events:
            evs = list(evts)
            if len(evs) == 1:
                evt = formatters.get(evs[0].action)(evs[0])
            else:
                evt = formatters.get("group")(self.view.object, evs)
            _events.append(evt)
        ctx["contributors"] = [
            profile.get(contrib.__class__)(contrib)
            for contrib
            in event_log.get_contributors()]
        n = 10
        if n is not None:
            _events = _events[-n:]
        ctx["events"] = reversed(_events)
        return ctx
