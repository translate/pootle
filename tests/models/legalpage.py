#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL2
# license. See the LICENSE file for a copy of the license and the AUTHORS file
# for copyright and authorship information.

import pytest

from pootle.core.utils.timezone import aware_datetime
from staticpages.models import LegalPage

from ..factories import AgreementFactory, LegalPageFactory, UserFactory


@pytest.mark.xfail
@pytest.mark.django_db()
def test_pending_agreements():
    """Tests proper user pending agreements are returned."""
    foo_user = UserFactory.create(username='foo')

    # XXX: for some obscure reason calling `LegalPageFactory.create()`
    # twice to create two object instances has weird effects in Django's
    # queryset caching: `len()`, and therefore `.count()`, always returns
    # the same value. Using `.create_batch()` here as a workaround
    privacy_policy, tos = LegalPageFactory.create_batch(2, active=True)
    privacy_policy.modified_on = aware_datetime(2014, 01, 01)
    privacy_policy.save()
    tos.modified_on = aware_datetime(2015, 01, 01)
    tos.save()

    # `foo_user` hasn't agreed any ToS yet
    pending = LegalPage.objects.pending_user_agreement(foo_user)
    assert len(pending) == 2
    assert privacy_policy in pending
    assert tos in pending

    # `foo_user` agreed the privacy policy
    AgreementFactory.create(
        user=foo_user,
        document=privacy_policy,
        agreed_on=aware_datetime(2014, 02, 02),
    )

    pending = LegalPage.objects.pending_user_agreement(foo_user)
    assert len(pending) == 1
    assert tos in pending

    # `foo_user` also accepted the ToS
    AgreementFactory.create(
        user=foo_user,
        document=tos,
        agreed_on=aware_datetime(2015, 02, 02),
    )

    pending = LegalPage.objects.pending_user_agreement(foo_user)
    assert len(pending) == 0

    # The ToS were modified, `foo_user` must agree it
    tos.modified_on = aware_datetime(2015, 03, 03)
    tos.save()

    pending = LegalPage.objects.pending_user_agreement(foo_user)
    assert len(pending) == 1
    assert tos in pending
