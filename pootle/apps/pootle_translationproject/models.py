# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import logging
import posixpath
from pathlib import PurePosixPath

from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.urls import reverse
from django.utils.functional import cached_property

from pootle.core.delegate import data_tool
from pootle.core.mixins import CachedTreeItem
from pootle.core.url_helpers import get_editor_filter, split_pootle_path
from pootle_app.models.directory import Directory
from pootle_checks.constants import EXCLUDED_FILTERS
from pootle_language.models import Language
from pootle_project.models import Project
from pootle_revision.models import Revision
from staticpages.models import StaticPage


logger = logging.getLogger(__name__)


class TranslationProjectManager(models.Manager):

    def get_terminology_project(self, language_id):
        # FIXME: the code below currently uses the same approach to determine
        # the 'terminology' kind of a project as 'Project.is_terminology()',
        # which means it checks the value of 'checkstyle' field
        # (see pootle_project/models.py:240).
        #
        # This should probably be replaced in the future with a dedicated
        # project property.
        return self.get(language=language_id,
                        project__checkstyle='terminology')

    def live(self):
        """Filters translation projects that have non-obsolete directories."""
        return self.filter(directory__obsolete=False)

    def for_user(self, user, select_related=None):
        """Filters translation projects for a specific user.

        - Admins always get all translation projects.
        - Regular users only get enabled translation projects
            accessible to them.

        :param user: The user for whom the translation projects need to be
            retrieved for.
        :return: A filtered queryset with `TranslationProject`s for `user`.
        """
        qs = self.live()
        if select_related is not None:
            qs = qs.select_related(*select_related)

        if user.is_superuser:
            return qs

        return qs.filter(
            project__disabled=False,
            project__code__in=Project.accessible_by_user(user))

    def get_for_user(self, user, project_code, language_code,
                     select_related=None):
        """Gets a `language_code`/`project_code` translation project
        for a specific `user`.

        - Admins can get the translation project even
            if its project is disabled.
        - Regular users only get a translation project
            if its project isn't disabled and it is accessible to them.

        :param user: The user for whom the translation project needs
            to be retrieved.
        :param project_code: The code of a project for the TP to retrieve.
        :param language_code: The code of the language fro the TP to retrieve.
        :return: The `TranslationProject` matching the params, raises
            otherwise.
        """
        return self.for_user(
            user, select_related).get(
                project__code=project_code,
                language__code=language_code)


class TranslationProject(models.Model, CachedTreeItem):

    language = models.ForeignKey(
        Language, db_index=False, on_delete=models.CASCADE)
    project = models.ForeignKey(
        Project, db_index=True, on_delete=models.CASCADE)
    directory = models.OneToOneField(
        Directory, db_index=True, editable=False, on_delete=models.CASCADE)
    pootle_path = models.CharField(max_length=255, null=False, unique=True,
                                   db_index=True, editable=False)
    creation_time = models.DateTimeField(auto_now_add=True, db_index=True,
                                         editable=False, null=True)
    revisions = GenericRelation(Revision)

    objects = TranslationProjectManager()

    class Meta(object):
        unique_together = (
            ('language', 'project'),
            ('project', 'language'))
        db_table = 'pootle_app_translationproject'
        # disabled objects are hidden for related objects too
        base_manager_name = 'objects'

    @cached_property
    def code(self):
        return u'-'.join([self.language.code, self.project.code])

    @cached_property
    def data_tool(self):
        return data_tool.get(self.__class__)(self)

    # # # # # # # # # # # # # #  Properties # # # # # # # # # # # # # # # # # #

    @property
    def name(self):
        # TODO: See if `self.fullname` can be removed
        return self.fullname

    @property
    def fullname(self):
        return "%s [%s]" % (self.project.fullname, self.language.name)

    @property
    def checker(self):
        from translate.filters import checks
        checkerclasses = [
            checks.projectcheckers.get(
                self.project.checkstyle,
                checks.StandardChecker)]
        return checks.TeeChecker(checkerclasses=checkerclasses,
                                 excludefilters=EXCLUDED_FILTERS,
                                 errorhandler=self.filtererrorhandler,
                                 languagecode=self.language.code)

    @property
    def disabled(self):
        return self.project.disabled

    @cached_property
    def templates_tp(self):
        return self.project.get_template_translationproject()

    @property
    def is_template_project(self):
        return self == self.templates_tp

    # # # # # # # # # # # # # #  Methods # # # # # # # # # # # # # # # # # # #

    def __unicode__(self):
        return self.pootle_path

    def __init__(self, *args, **kwargs):
        super(TranslationProject, self).__init__(*args, **kwargs)

    def save(self, *args, **kwargs):
        self.directory = (
            self.language.directory.get_or_make_subdir(self.project.code))
        self.pootle_path = self.directory.pootle_path
        super(TranslationProject, self).save(*args, **kwargs)
        if self.directory.tp_id != self.pk:
            self.directory.tp = self
            self.directory.save()

    def delete(self, *args, **kwargs):
        directory = self.directory

        super(TranslationProject, self).delete(*args, **kwargs)
        directory.delete()

    def get_absolute_url(self):
        return reverse(
            'pootle-tp-browse',
            args=split_pootle_path(self.pootle_path)[:-1])

    def get_translate_url(self, **kwargs):
        return u''.join(
            [reverse("pootle-tp-translate",
                     args=split_pootle_path(self.pootle_path)[:-1]),
             get_editor_filter(**kwargs)])

    def get_announcement(self, user=None):
        """Return the related announcement, if any."""
        return StaticPage.get_announcement_for(self.pootle_path, user)

    def filtererrorhandler(self, functionname, str1, str2, e):
        logger.error(
            u"Error in filter %s: %r, %r, %s",
            functionname,
            str1,
            str2, e)
        return False

    def is_accessible_by(self, user):
        """Returns `True` if the current translation project is accessible
        by `user`.
        """
        if user.is_superuser:
            return True

        return self.project.code in Project.accessible_by_user(user)

    def can_be_inited_from_templates(self):
        """Returns `True` if the current translation project hasn't been
        saved yet and can be initialized from templates.
        """

        # This method checks if the current translation project directory
        # doesn't exist. So it won't work if the translation project is already
        # saved the database because the translation project directory is
        # auto-created in `save()` method.
        return (
            not self.is_template_project
            and self.templates_tp is not None)

    def create_parent_dirs(self, pootle_path):
        parent = self.directory
        dirs_to_create = []
        for path in PurePosixPath(pootle_path).parents:
            path = posixpath.join(str(path), "")
            if path == self.pootle_path:
                break
            dirs_to_create.append(path)
        for path in reversed(dirs_to_create):
            parent, __ = Directory.objects.get_or_create(
                pootle_path=path,
                parent=parent,
                tp=self,
                name=posixpath.basename(path.rstrip("/")))
        return parent

    def init_store_from_template(self, template_store):
        """Initialize a new file for `self` using `template_store`.
        """
        pootle_path = posixpath.join(
            self.pootle_path.rstrip("/"),
            template_store.tp_path.lstrip("/"))
        pootle_path = ".".join(
            [posixpath.splitext(pootle_path)[0],
             template_store.filetype.extension.name])
        name = posixpath.basename(pootle_path)
        if self.project.is_gnustyle:
            # gnu-style layout
            # use language code instead of template name
            name = ".".join(
                [self.language.code,
                 template_store.filetype.extension.name])
            dirname = posixpath.dirname(pootle_path)
            pootle_path = posixpath.join(dirname, name)
        if not self.stores.filter(pootle_path=pootle_path).exists():
            return self.stores.create(
                parent=self.create_parent_dirs(pootle_path),
                pootle_path=pootle_path,
                name=name)

    def init_from_templates(self):
        """Initializes the current translation project files using
        the templates TP ones.
        """
        template_stores = self.templates_tp.stores.live().select_related(
            "filetype__template_extension",
            "filetype__extension").order_by("creation_time")
        for template_store in template_stores.iterator():
            new_store = self.init_store_from_template(template_store)
            if new_store:
                new_store.update(
                    new_store.deserialize(template_store.serialize()))

    # # # TreeItem
    def get_children(self):
        return self.directory.children

    def get_parents(self):
        return [self.project]
