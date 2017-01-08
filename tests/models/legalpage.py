# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from pytest_pootle.factories import (AgreementFactory, LegalPageFactory,
                                     UserFactory)

from pootle.core.utils.timezone import aware_datetime
from staticpages.models import LegalPage


@pytest.mark.django_db
@pytest.mark.xfail(reason="this will be dropped")
def test_pending_agreements():
    """Tests proper user pending agreements are returned."""
    foo_user = UserFactory.create(username='foo')

    privacy_policy = LegalPageFactory.create(
        active=True,
        modified_on=aware_datetime(2014, 1, 1),
    )

    # `foo_user` hasn't agreed the privacy policy yet
    pending = list(LegalPage.objects.pending_user_agreement(foo_user))
    assert len(pending) == 1
    assert privacy_policy in pending

    # `foo_user` agreed the privacy policy
    AgreementFactory.create(
        user=foo_user,
        document=privacy_policy,
        agreed_on=aware_datetime(2014, 2, 2),
    )

    pending = list(LegalPage.objects.pending_user_agreement(foo_user))
    assert len(pending) == 0

    # Let's add a new ToS
    tos = LegalPageFactory.create(
        active=True,
        modified_on=aware_datetime(2015, 1, 1),
    )

    pending = list(LegalPage.objects.pending_user_agreement(foo_user))
    assert len(pending) == 1
    assert tos in pending

    # `foo_user` also accepted the ToS
    AgreementFactory.create(
        user=foo_user,
        document=tos,
        agreed_on=aware_datetime(2015, 2, 2),
    )

    pending = list(LegalPage.objects.pending_user_agreement(foo_user))
    assert len(pending) == 0

    # The ToS were modified, `foo_user` must agree it
    tos.modified_on = aware_datetime(2015, 3, 3)
    tos.save()

    pending = list(LegalPage.objects.pending_user_agreement(foo_user))
    assert len(pending) == 1
    assert tos in pending

    # Same with the privacy policy
    privacy_policy.modified_on = aware_datetime(2015, 4, 4)
    privacy_policy.save()

    pending = list(LegalPage.objects.pending_user_agreement(foo_user))
    assert len(pending) == 2
    assert privacy_policy in pending
    assert tos in pending

    # Let's disable the ToS
    tos.active = False
    tos.save()

    pending = list(LegalPage.objects.pending_user_agreement(foo_user))
    assert len(pending) == 1
    assert privacy_policy in pending
