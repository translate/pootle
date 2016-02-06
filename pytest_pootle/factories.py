#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from hashlib import md5

import factory

from django.utils import timezone

import pootle_store


class ScoreLogFactory(factory.django.DjangoModelFactory):
    creation_time = timezone.now()

    class Meta(object):
        model = 'pootle_statistics.ScoreLog'


class SubmissionFactory(factory.django.DjangoModelFactory):
    creation_time = timezone.now()

    class Meta(object):
        model = 'pootle_statistics.Submission'


class UserFactory(factory.django.DjangoModelFactory):
    username = factory.Sequence(lambda n: 'foo%s' % n)
    email = factory.LazyAttribute(lambda o: '%s@example.org' % o.username)

    class Meta(object):
        model = 'accounts.User'


class LegalPageFactory(factory.django.DjangoModelFactory):
    title = factory.Sequence(lambda n: 'title%s' % n)
    virtual_path = factory.Sequence(lambda n: '/foo/bar%s' % n)

    class Meta(object):
        model = 'staticpages.LegalPage'


class AgreementFactory(factory.django.DjangoModelFactory):
    user = factory.SubFactory(UserFactory)
    document = factory.SubFactory(LegalPageFactory)

    class Meta(object):
        model = 'staticpages.Agreement'


class DirectoryFactory(factory.django.DjangoModelFactory):

    @factory.lazy_attribute
    def pootle_path(self):
        if self.parent is None:
            return "/"
        return (
            "%s/%s"
            % (self.parent.pootle_path.rstrip("/"),
               self.name))

    class Meta(object):
        model = 'pootle_app.Directory'
        django_get_or_create = ("name", "parent")

    obsolete = False


class LanguageFactory(factory.django.DjangoModelFactory):

    class Meta(object):
        model = 'pootle_language.Language'
        django_get_or_create = ("code", )

    @factory.lazy_attribute
    def code(self):
        from pootle_language.models import Language

        # returns an incrementing index relative to the tp
        return 'language%s' % Language.objects.count()

    @factory.lazy_attribute
    def fullname(self):
        from pootle_language.models import Language

        # returns an incrementing index relative to the tp
        return 'Language %s' % Language.objects.count()


class ProjectFactory(factory.django.DjangoModelFactory):

    class Meta(object):
        model = 'pootle_project.Project'
        django_get_or_create = ("code", )

    @factory.lazy_attribute
    def code(self):
        from pootle_project.models import Project

        # returns an incrementing index relative to the tp
        return 'project%s' % Project.objects.count()

    @factory.lazy_attribute
    def fullname(self):
        from pootle_project.models import Project

        # returns an incrementing index relative to the tp
        return 'Project %s' % Project.objects.count()

    pootle_path = factory.LazyAttribute(lambda p: "/projects/%s" % p.code)


class StoreFactory(factory.django.DjangoModelFactory):

    class Meta(object):
        model = 'pootle_store.Store'
        django_get_or_create = ("pootle_path", )

    parent = factory.LazyAttribute(
        lambda s: s.translation_project.directory)

    @factory.lazy_attribute
    def pootle_path(self):
        return (
            "%s/%s"
            % (self.translation_project.pootle_path.rstrip("/"),
               self.name))

    @factory.lazy_attribute
    def name(self):
        # returns an incrementing index relative to the tp
        return 'store%s.po' % self.translation_project.stores.count()


class TranslationProjectFactory(factory.django.DjangoModelFactory):

    class Meta(object):
        model = 'pootle_translationproject.TranslationProject'


class UnitFactory(factory.django.DjangoModelFactory):

    class Meta(object):
        model = 'pootle_store.Unit'

    state = pootle_store.util.UNTRANSLATED

    @factory.lazy_attribute
    def index(self):
        # returns an incrementing index relative to the store
        return self.store.unit_set.count()

    @factory.lazy_attribute
    def unitid(self):
        return (
            "%s_unit%s"
            % (pootle_store.util.get_state_name(self),
               self.index))

    @factory.lazy_attribute
    def unitid_hash(self):
        return md5(self.unitid.encode("utf-8")).hexdigest()

    @factory.lazy_attribute
    def source_f(self):
        return (
            "%s Source %s %s"
            % (pootle_store.util.get_state_name(self.state).capitalize(),
               self.store.pootle_path,
               self.index))

    @factory.lazy_attribute
    def target_f(self):
        state_name = pootle_store.util.get_state_name(self.state)
        if state_name in ["translated", "fuzzy", "obsolete"]:
            return (
                "%s Target %s %s"
                % (state_name.capitalize(),
                   self.store.pootle_path,
                   self.index))
        return ""


class VirtualFolderFactory(factory.django.DjangoModelFactory):

    class Meta(object):
        model = 'virtualfolder.VirtualFolder'
        django_get_or_create = ("location", "filter_rules")

    priority = 2
    is_public = True
    location = "/{LANG}/{PROJ}/"

    @factory.lazy_attribute
    def name(self):
        from virtualfolder.models import VirtualFolder

        return 'virtualfolder%s' % VirtualFolder.objects.count()


class AnnouncementFactory(factory.django.DjangoModelFactory):

    class Meta(object):
        model = 'staticpages.StaticPage'
    active = True


class SuggestionFactory(factory.django.DjangoModelFactory):

    class Meta(object):
        model = 'pootle_store.Suggestion'
