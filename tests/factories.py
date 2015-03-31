#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import factory

from django.utils import timezone


class SubmissionFactory(factory.django.DjangoModelFactory):
    FACTORY_FOR = 'pootle_statistics.Submission'

    creation_time = timezone.now()


class UserFactory(factory.django.DjangoModelFactory):
    FACTORY_FOR = 'accounts.User'

    username = factory.Sequence(lambda n: 'foo%s' % n)
    email = factory.LazyAttribute(lambda o: '%s@example.org' % o.username)


class LegalPageFactory(factory.django.DjangoModelFactory):
    FACTORY_FOR = 'staticpages.LegalPage'

    title = factory.Sequence(lambda n: 'title%s' % n)
    virtual_path = factory.Sequence(lambda n: '/foo/bar%s' % n)

    class Meta:
        abstract = True


class AgreementFactory(factory.django.DjangoModelFactory):
    FACTORY_FOR = 'staticpages.Agreement'

    user = factory.SubFactory(UserFactory)
    document = factory.SubFactory(LegalPageFactory)
