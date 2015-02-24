#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2014-2015 Evernote Corporation
#
# This file is part of Pootle.
#
# Pootle is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.

import factory

from django.utils import timezone


class SubmissionFactory(factory.django.DjangoModelFactory):
    FACTORY_FOR = 'pootle_statistics.Submission'

    creation_time = timezone.now()


class EvernoteAccountFactory(factory.django.DjangoModelFactory):
    FACTORY_FOR = 'evernote_auth.EvernoteAccount'


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
