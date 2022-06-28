# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from pootle.i18n.gettext import ugettext as _
from pootle_log.formatters import (
    FormattedEvent, FormattedSubmissionEvent, UnitCreatedEvent)


class StoreUnitCreatedEvent(UnitCreatedEvent):
    pass


class StoreUnitStateChangedEvent(FormattedSubmissionEvent):

    @property
    def message(self):
        return _("State changed")


class StoreUnitTargetUpdatedEvent(FormattedSubmissionEvent):

    @property
    def message(self):
        return _("Translation updated")


class StoreSuggestionAddedEvent(FormattedEvent):

    @property
    def message(self):
        return _("Suggestion added")

    @property
    def method(self):
        return ""


class StoreSuggestionAcceptedEvent(FormattedEvent):

    @property
    def message(self):
        return _("Suggestion accepted")

    @property
    def method(self):
        return ""


class StoreSuggestionRejectedEvent(FormattedEvent):

    @property
    def message(self):
        return _("Suggestion rejected")

    @property
    def method(self):
        return ""
