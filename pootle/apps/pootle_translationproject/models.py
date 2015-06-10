#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009-2013 Zuza Software Foundation
# Copyright 2013-2014 Evernote Corporation
#
# This file is part of Pootle.
#
# This program is free software; you can redistribute it and/or modify
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

import logging
import os
from itertools import chain

from translate.misc.lru import LRUCachingDict
from translate.storage.base import ParseError

from django.conf import settings
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.db import models, IntegrityError
from django.db.models import Q
from django.db.models.signals import post_save
from django.utils import dateformat
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _

from pootle.core.managers import RelatedManager
from pootle.core.mixins import TreeItem
from pootle.core.url_helpers import get_editor_filter, split_pootle_path
from pootle_app.models.directory import Directory
from pootle_language.models import Language
from pootle_misc.checks import excluded_filters
from pootle_misc.stats import stats_message_raw
from pootle_project.models import Project
from pootle_statistics.models import Submission
from pootle_store.models import Store, Unit, PARSED
from pootle_store.util import (absolute_real_path, relative_real_path,
                               OBSOLETE)


class TranslationProjectNonDBState(object):

    def __init__(self, parent):
        self.parent = parent

        # Terminology matcher
        self.termmatcher = None
        self.termmatchermtime = None

        self._indexing_enabled = True
        self._index_initialized = False
        self.indexer = None


def create_or_resurrect_translation_project(language, project):
    tp = create_translation_project(language, project)
    if tp is not None:
        if tp.directory.obsolete:
            tp.directory.obsolete = False
            tp.directory.save()
            logging.info(u"Resurrected %s", tp)
        else:
            logging.info(u"Created %s", tp)


def create_translation_project(language, project):
    from pootle_app import project_tree
    if project_tree.translation_project_should_exist(language, project):
        try:
            translation_project, created = TranslationProject.objects.all() \
                    .get_or_create(language=language, project=project)
            return translation_project
        except (OSError, IndexError):
            return None


def scan_translation_projects():
    for language in Language.objects.iterator():
        for project in Project.objects.iterator():
            create_translation_project(language, project)


class VersionControlError(Exception):
    pass


class TranslationProjectManager(RelatedManager):
    # disabled objects are hidden for related objects too
    use_for_related_fields = True

    def live(self):
        """Filters translation projects that have non-obsolete directories
        and they belong to enabled projects."""
        return self.filter(directory__obsolete=False, project__disabled=False)

    def disabled(self):
        """Filters translation projects that have obsolete directories or they
        belong to disabled projects."""
        return self.filter(Q(directory__obsolete=True) | Q(project__disabled=True))


class TranslationProject(models.Model, TreeItem):

    language = models.ForeignKey(Language, db_index=True)
    project = models.ForeignKey(Project, db_index=True)
    real_path = models.FilePathField(editable=False)
    directory = models.OneToOneField(Directory, db_index=True, editable=False)
    pootle_path = models.CharField(
        max_length=255,
        null=False,
        unique=True,
        db_index=True,
        editable=False,
    )
    creation_time = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        editable=False,
        null=True,
    )

    _non_db_state_cache = LRUCachingDict(settings.PARSE_POOL_SIZE,
                                         settings.PARSE_POOL_CULL_FREQUENCY)

    index_directory = ".translation_index"

    objects = TranslationProjectManager()

    class Meta:
        unique_together = ('language', 'project')
        db_table = 'pootle_app_translationproject'

    ############################ Properties ###################################

    @property
    def name(self):
        # TODO: See if `self.fullname` can be removed
        return self.fullname

    @property
    def fullname(self):
        return "%s [%s]" % (self.project.fullname, self.language.name)

    @property
    def abs_real_path(self):
        return absolute_real_path(self.real_path)

    @abs_real_path.setter
    def abs_real_path(self, value):
        self.real_path = relative_real_path(value)

    @property
    def file_style(self):
        return self.project.get_treestyle()

    @property
    def checker(self):
        from translate.filters import checks
        checkerclasses = [checks.projectcheckers.get(self.project.checkstyle,
                                                     checks.StandardChecker),
                          checks.StandardUnitChecker]

        return checks.TeeChecker(checkerclasses=checkerclasses,
                                 excludefilters=excluded_filters,
                                 errorhandler=self.filtererrorhandler,
                                 languagecode=self.language.code)

    @property
    def non_db_state(self):
        if not hasattr(self, "_non_db_state"):
            try:
                self._non_db_state = self._non_db_state_cache[self.id]
            except KeyError:
                self._non_db_state = TranslationProjectNonDBState(self)
                self._non_db_state_cache[self.id] = \
                        TranslationProjectNonDBState(self)

        return self._non_db_state

    @property
    def units(self):
        self.require_units()
        # FIXME: we rely on implicit ordering defined in the model. We might
        # want to consider pootle_path as well
        return Unit.objects.filter(store__translation_project=self,
                                   state__gt=OBSOLETE).select_related('store')

    @property
    def is_terminology_project(self):
        return self.pootle_path.endswith('/terminology/')

    @property
    def is_template_project(self):
        return self == self.project.get_template_translationproject()

    @property
    def indexer(self):
        if (self.non_db_state.indexer is None and
            self.non_db_state._indexing_enabled):
            try:
                indexer = self.make_indexer()

                if not self.non_db_state._index_initialized:
                    self.init_index(indexer)
                    self.non_db_state._index_initialized = True

                self.non_db_state.indexer = indexer
            except Exception as e:
                logging.warning(u"Could not initialize indexer for %s in %s: "
                                u"%s", self.project.code, self.language.code,
                                str(e))
                self.non_db_state._indexing_enabled = False

        return self.non_db_state.indexer

    @property
    def has_index(self):
        return (self.non_db_state._indexing_enabled and
                (self.non_db_state._index_initialized or
                 self.indexer is not None))

    ############################ Cached properties ############################

    @cached_property
    def code(self):
        return u'-'.join([self.language.code, self.project.code])

    ############################ Methods ######################################

    def __unicode__(self):
        return self.pootle_path

    def __init__(self, *args, **kwargs):
        super(TranslationProject, self).__init__(*args, **kwargs)

    def save(self, *args, **kwargs):
        created = self.id is None

        self.directory = self.language.directory \
                                      .get_or_make_subdir(self.project.code)
        self.pootle_path = self.directory.pootle_path

        project_dir = self.project.get_real_path()
        from pootle_app.project_tree import get_translation_project_dir
        self.abs_real_path = get_translation_project_dir(self.language,
             project_dir, self.file_style,
             make_dirs=not self.directory.obsolete)

        super(TranslationProject, self).save(*args, **kwargs)

        if created:
            self.scan_files()

    def delete(self, *args, **kwargs):
        directory = self.directory

        super(TranslationProject, self).delete(*args, **kwargs)
        #TODO: avoid an access to directory while flushing the cache
        directory.flush_cache()
        directory.delete()

    def get_absolute_url(self):
        lang, proj, dir, fn = split_pootle_path(self.pootle_path)
        return reverse('pootle-tp-overview', args=[lang, proj, dir, fn])

    def get_translate_url(self, **kwargs):
        lang, proj, dir, fn = split_pootle_path(self.pootle_path)
        return u''.join([
            reverse('pootle-tp-translate', args=[lang, proj, dir, fn]),
            get_editor_filter(**kwargs),
        ])

    def filtererrorhandler(self, functionname, str1, str2, e):
        logging.error(u"Error in filter %s: %r, %r, %s", functionname, str1,
                      str2, e)
        return False

    def is_accessible_by(self, user):
        """Returns `True` if the current translation project is accessible
        by `user`.
        """
        if user.is_superuser:
            return True

        return self.project.code in Project.accessible_by_user(user)

    def update(self):
        """Update all stores to reflect state on disk."""
        stores = self.stores.exclude(file='').filter(state__gte=PARSED)
        for store in stores.iterator():
            store.update(update_translation=True, update_structure=True)

    def sync(self, conservative=True, skip_missing=False, modified_since=0):
        """Sync unsaved work on all stores to disk."""
        stores = self.stores.exclude(file='').filter(state__gte=PARSED)
        for store in stores.iterator():
            store.sync(update_translation=True,
                       update_structure=not conservative,
                       conservative=conservative, create=False,
                       skip_missing=skip_missing,
                       modified_since=modified_since)

    def get_mtime(self):
        return self.directory.get_mtime()

    def require_units(self):
        """Makes sure all stores are parsed"""
        errors = 0
        for store in self.stores.filter(state__lt=PARSED).iterator():
            try:
                store.require_units()
            except IntegrityError:
                logging.info(u"Duplicate IDs in %s", store.abs_real_path)
                errors += 1
            except ParseError as e:
                logging.info(u"Failed to parse %s\n%s", store.abs_real_path, e)
                errors += 1
            except (IOError, OSError) as e:
                logging.info(u"Can't access %s\n%s", store.abs_real_path, e)
                errors += 1

        return errors

    ### TreeItem

    def get_children_for_stats(self):
        return super(TranslationProject, self).get_children_for_stats()

    def get_progeny(self):
        return super(TranslationProject, self).get_progeny()

    def get_self_stats(self):
        return super(TranslationProject, self).get_self_stats()

    def get_children(self):
        return self.directory.get_children()

    def get_total_wordcount(self):
        return self.total_wordcount

    def get_translated_wordcount(self):
        return self.translated_wordcount

    def get_fuzzy_wordcount(self):
        return self.fuzzy_wordcount

    def get_suggestion_count(self):
        return self.suggestion_count

    def get_critical_error_unit_count(self):
        return self.failing_critical_count

    def get_last_updated(self):
        if self.last_unit is None:
            return {'id': 0, 'creation_time': 0, 'snippet': ''}

        creation_time = dateformat.format(self.last_unit.creation_time, 'U')
        return {
            'id': self.last_unit.id,
            'creation_time': int(creation_time),
            'snippet': self.last_unit.get_last_updated_message()
        }

    def get_last_action(self):
        try:
            if (self.last_submission is None or
                (self.last_submission is not None and
                 self.last_submission.unit is None)):
                return {'id': 0, 'mtime': 0, 'snippet': ''}
        except Submission.DoesNotExist:
            return {'id': 0, 'mtime': 0, 'snippet': ''}

        mtime = dateformat.format(self.last_submission.creation_time, 'U')
        return {
            'id': self.last_submission.unit.id,
            'mtime': int(mtime),
            'snippet': self.last_submission.get_submission_message()
        }

    def get_cachekey(self):
        return self.directory.pootle_path

    def get_parents(self):
        return [self.language, self.project]

    ### /TreeItem

    def update_against_templates(self, pootle_path=None):
        """Update translation project from templates."""

        if self.is_template_project:
            return

        template_translation_project = self.project \
                                           .get_template_translationproject()

        if (template_translation_project is None or
            template_translation_project == self):
            return

        monolingual = self.project.is_monolingual

        if not monolingual:
            self.sync()

        from pootle_app.project_tree import (convert_template,
                                             get_translated_name,
                                             get_translated_name_gnu)

        for store in template_translation_project.stores.iterator():
            if self.file_style == 'gnu':
                new_pootle_path, new_path = get_translated_name_gnu(self, store)
            else:
                new_pootle_path, new_path = get_translated_name(self, store)

            if pootle_path is not None and new_pootle_path != pootle_path:
                continue

            try:
                from pootle.scripts import hooks
                relative_po_path = os.path.relpath(new_path,
                                                   settings.PODIRECTORY)
                if not hooks.hook(self.project.code, "pretemplateupdate",
                                  relative_po_path):
                    continue
            except:
                # Assume hook is not present.
                pass

            convert_template(self, store, new_pootle_path, new_path,
                             monolingual)

        all_files, new_files = self.scan_files(vcs_sync=False)

        from pootle_misc import versioncontrol
        project_path = self.project.get_real_path()

        if new_files and versioncontrol.hasversioning(project_path):
            from pootle.scripts import hooks

            message = ("New files added from %s based on templates" %
                       settings.TITLE)

            filestocommit = []
            for new_file in new_files:
                try:
                    hook_files = hooks.hook(self.project.code, "precommit",
                                            new_file.file.name, author=None,
                                            message=message)
                    filestocommit.extend(hook_files)
                except ImportError:
                    # Failed to import the hook - we're going to assume there
                    # just isn't a hook to import. That means we'll commit the
                    # original file.
                    filestocommit.append(new_file.file.name)

            success = True
            try:
                output = versioncontrol.add_files(project_path, filestocommit,
                                                  message)
            except Exception:
                logging.exception(u"Failed to add files")
                success = False

            for new_file in new_files:
                try:
                    hooks.hook(self.project.code, "postcommit",
                               new_file.file.name, success=success)
                except:
                    #FIXME: We should not hide the exception - makes
                    # development impossible
                    pass

        if pootle_path is None:
            from pootle_app.signals import post_template_update
            post_template_update.send(sender=self)

    def scan_files(self, vcs_sync=True):
        """Scan the file system and return a list of translation files.

        :param vcs_sync: boolean on whether or not to synchronise the PO
                         directory with the VCS checkout.
        """
        projects = [p.strip() for p in self.project.ignoredfiles.split(',')]
        ignored_files = set(projects)
        ext = os.extsep + self.project.localfiletype

        # Scan for pots if template project
        if self.is_template_project:
            ext = os.extsep + self.project.get_template_filetype()

        from pootle_app.project_tree import (add_files,
                                             match_template_filename,
                                             direct_language_match_filename,
                                             sync_from_vcs)

        all_files = []
        new_files = []

        if self.file_style == 'gnu':
            if self.pootle_path.startswith('/templates/'):
                file_filter = lambda filename: match_template_filename(
                                    self.project, filename,
                              )
            else:
                file_filter = lambda filename: direct_language_match_filename(
                                    self.language.code, filename,
                              )
        else:
            file_filter = lambda filename: True

        if vcs_sync:
            sync_from_vcs(ignored_files, ext, self.real_path, file_filter)

        all_files, new_files = add_files(
                self,
                ignored_files,
                ext,
                self.real_path,
                self.directory,
                file_filter,
        )

        return all_files, new_files

    def update_file_from_version_control(self, store):
        from pootle.scripts import hooks
        store.sync(update_translation=True)

        filetoupdate = store.file.name
        try:
            filetoupdate = hooks.hook(self.project.code, "preupdate",
                                      store.file.name)
        except:
            pass

        # Keep a copy of working files in memory before updating
        working_copy = store.file.store

        try:
            logging.debug(u"Updating %s from version control", store.file.name)
            from pootle_misc import versioncontrol
            versioncontrol.update_file(filetoupdate)
            store.file._delete_store_cache()
            store.file._update_store_cache()
        except Exception:
            # Something wrong, file potentially modified, bail out
            # and replace with working copy
            logging.exception(u"Near fatal catastrophe, while updating %s "
                              u"from version control", store.file.name)
            working_copy.save()

            raise VersionControlError

        try:
            hooks.hook(self.project.code, "postupdate", store.file.name)
        except:
            pass

        try:
            logging.debug(u"Parsing version control copy of %s into db",
                          store.file.name)
            store.update(update_structure=True, update_translation=True)

            #FIXME: try to avoid merging if file was not updated
            logging.debug(u"Merging %s with version control update",
                          store.file.name)
            store.mergefile(working_copy, None, allownewstrings=False,
                            suggestions=True, notranslate=False,
                            obsoletemissing=False)
        except Exception:
            logging.exception(u"Near fatal catastrophe, while merging %s with "
                              u"version control copy", store.file.name)
            working_copy.save()
            store.update(update_structure=True, update_translation=True)
            raise

    def update_dir(self, request=None, directory=None):
        """Updates translation project's files from version control, retaining
        uncommitted translations.
        """
        remote_stats = {}

        from pootle_misc import versioncontrol
        try:
            versioncontrol.update_dir(self.real_path)
        except IOError as e:
            logging.exception(u"Error during update of %s", self.real_path)
            if request:
                msg = _("Failed to update from version control: %(error)s",
                        {"error": e})
                messages.error(request, msg)
            return

        all_files, new_files = self.scan_files()
        new_file_set = set(new_files)

        from pootle.scripts import hooks

        # Go through all stores except any pootle-terminology.* ones
        if directory.is_translationproject():
            stores = self.stores.exclude(file="")
        else:
            stores = directory.stores.exclude(file="")

        for store in stores.iterator():
            if store in new_file_set:
                continue

            store.sync(update_translation=True)
            filetoupdate = store.file.name
            try:
                filetoupdate = hooks.hook(self.project.code, "preupdate",
                                          store.file.name)
            except:
                pass

            # keep a copy of working files in memory before updating
            working_copy = store.file.store

            versioncontrol.copy_to_podir(filetoupdate)
            store.file._delete_store_cache()
            store.file._update_store_cache()

            try:
                hooks.hook(self.project.code, "postupdate",
                           store.file.name)
            except:
                pass

            try:
                logging.debug(u"Parsing version control copy of %s into db",
                              store.file.name)
                store.update(update_structure=True, update_translation=True)

                #FIXME: Try to avoid merging if file was not updated
                logging.debug(u"Merging %s with version control update",
                              store.file.name)
                store.mergefile(working_copy, None, allownewstrings=False,
                                suggestions=True, notranslate=False,
                                obsoletemissing=False)
            except Exception:
                logging.exception(u"Near fatal catastrophe, while merging %s "
                                  "with version control copy", store.file.name)
                working_copy.save()
                store.update(update_structure=True, update_translation=True)
                raise

        if request:
            msg = \
                _(u'Updated project <em>%(project)s</em> from version control',
                  {'project': self.fullname})
            messages.info(request, msg)

        from pootle_app.signals import post_vc_update
        post_vc_update.send(sender=self)

    def update_file(self, request, store):
        """Updates file from version control, retaining uncommitted
        translations"""
        try:
            self.update_file_from_version_control(store)

            # FIXME: This belongs to views
            msg = _(u'Updated file <em>%(filename)s</em> from version control',
                    {'filename': store.file.name})
            messages.info(request, msg)

            from pootle_app.signals import post_vc_update
            post_vc_update.send(sender=self)
        except VersionControlError as e:
            # FIXME: This belongs to views
            msg = _(u"Failed to update <em>%(filename)s</em> from "
                    u"version control: %(error)s",
                    {
                        'filename': store.file.name,
                        'error': e,
                    }
            )
            messages.error(request, msg)

        self.scan_files()

    def commit_dir(self, user, directory, request=None):
        """Commits files under a directory to version control.

        This does not do permission checking.
        """
        self.sync()
        total = directory.get_total_wordcount()
        translated = directory.get_translated_wordcount()
        fuzzy = directory.get_fuzzy_wordcount()
        author = user.username

        message = stats_message_raw("Commit from %s by user %s." %
                                    (settings.TITLE, author),
                                    total, translated, fuzzy)

        # Try to append email as well, since some VCS does not allow omitting
        # it (ie. Git).
        if user.is_authenticated() and len(user.email):
            author += " <%s>" % user.email

        if directory.is_translationproject():
            stores = list(self.stores.exclude(file=""))
        else:
            stores = list(directory.stores.exclude(file=""))

        filestocommit = []

        from pootle.scripts import hooks
        for store in stores:
            try:
                filestocommit.extend(hooks.hook(self.project.code, "precommit",
                                                store.file.name, author=author,
                                                message=message)
                                    )
            except ImportError:
                # Failed to import the hook - we're going to assume there just
                # isn't a hook to import. That means we'll commit the original
                # file.
                filestocommit.append(store.file.name)

        success = True
        try:
            from pootle_misc import versioncontrol
            project_path = self.project.get_real_path()
            versioncontrol.add_files(project_path, filestocommit, message,
                                     author)
            # FIXME: This belongs to views
            if request is not None:
                msg = _("Committed all files under <em>%(path)s</em> to "
                        "version control", {'path': directory.pootle_path})
                messages.success(request, msg)
        except Exception as e:
            logging.exception(u"Failed to commit directory")

            # FIXME: This belongs to views
            if request is not None:
                msg = _("Failed to commit to version control: %(error)s",
                        {'error': e})
                messages.error(request, msg)

            success = False

        for store in stores:
            try:
                hooks.hook(self.project.code, "postcommit", store.file.name,
                           success=success)
            except:
                #FIXME: We should not hide the exception - makes development
                # impossible
                pass

        from pootle_app.signals import post_vc_commit
        post_vc_commit.send(sender=self, path_obj=directory,
                            user=user, success=success)

        return success

    def commit_file(self, user, store, request=None):
        """Commits an individual file to version control.

        This does not do permission checking.
        """
        from pootle_app.signals import post_vc_commit
        from pootle_misc import versioncontrol
        from pootle.scripts import hooks

        store.sync(update_structure=False, update_translation=True,
                   conservative=True)
        total = store.get_total_wordcount()
        translated = store.get_translated_wordcount()
        fuzzy = store.get_fuzzy_wordcount()
        author = user.username

        message = stats_message_raw("Commit from %s by user %s." % \
                (settings.TITLE, author), total, translated, fuzzy)

        # Try to append email as well, since some VCS does not allow omitting
        # it (ie. Git).
        if user.is_authenticated() and len(user.email):
            author += " <%s>" % user.email

        try:
            filestocommit = hooks.hook(self.project.code, "precommit",
                                       store.file.name, author=author,
                                       message=message)
        except ImportError:
            # Failed to import the hook - we're going to assume there just
            # isn't a hook to import. That means we'll commit the original
            # file.
            filestocommit = [store.file.name]

        success = True
        for file in filestocommit:
            try:
                versioncontrol.commit_file(file, message=message,
                                           author=author)

                # FIXME: This belongs to views
                if request is not None:
                    msg = _("Committed file <em>%(filename)s</em> to version "
                            "control", {'filename': file})
                    messages.success(request, msg)
            except Exception as e:
                logging.exception(u"Failed to commit file")

                # FIXME: This belongs to views
                if request is not None:
                    msg_params = {
                        "filename": file,
                        "error": e,
                    }
                    msg = _("Failed to commit <em>%(filename)s</em> to version "
                            "control: %(error)s", msg_params)
                    messages.error(request, msg)
                success = False

        try:
            hooks.hook(self.project.code, "postcommit", store.file.name,
                       success=success)
        except:
            #FIXME: We should not hide the exception - makes development
            # impossible
            pass

        post_vc_commit.send(sender=self, path_obj=store,
                            user=user, success=success)

        return success

    def initialize(self):
        try:
            from pootle.scripts import hooks
            hooks.hook(self.project.code, "initialize", self.real_path,
                    self.language.code)
        except Exception:
            logging.exception(u"Failed to initialize (%s)", self.language.code)

    ###########################################################################

    def get_archive(self, stores, path=None):
        """Returns an archive of the given files."""
        import shutil
        import subprocess
        from pootle_misc import ptempfile as tempfile

        tempzipfile = None
        archivecontents = None

        try:
            # Using zip command line is fast
            # The temporary file below is opened and immediately closed for
            # security reasons
            fd, tempzipfile = tempfile.mkstemp(prefix='pootle', suffix='.zip')
            os.close(fd)
            archivecontents = open(tempzipfile, "wb")

            file_list = u" ".join(
                store.abs_real_path[len(self.abs_real_path)+1:] \
                for store in stores.iterator()
            )
            process = subprocess.Popen(['zip', '-r', '-', file_list],
                                       cwd=self.abs_real_path,
                                       stdout=archivecontents)
            result = process.wait()

            if result == 0:
                if path is not None:
                    shutil.move(tempzipfile, path)
                    return
                else:
                    filedata = open(tempzipfile, "r").read()
                    if filedata:
                        return filedata
                    else:
                        raise Exception("failed to read temporary zip file")
            else:
                raise Exception("zip command returned error code: %d" % result)
        except Exception as e:
            # But if it doesn't work, we can do it from Python.
            logging.debug(e)
            logging.debug("falling back to zipfile module")
            if path is not None:
                if tempzipfile is None:
                    fd, tempzipfile = tempfile.mkstemp(prefix='pootle',
                                                       suffix='.zip')
                    os.close(fd)
                    archivecontents = open(tempzipfile, "wb")
            else:
                import cStringIO
                archivecontents = cStringIO.StringIO()

            import zipfile
            archive = zipfile.ZipFile(archivecontents, 'w',
                                      zipfile.ZIP_DEFLATED)
            for store in stores.iterator():
                archive.write(store.abs_real_path.encode('utf-8'),
                              store.abs_real_path[len(self.abs_real_path)+1:]
                                   .encode('utf-8'))
            archive.close()

            if path is not None:
                shutil.move(tempzipfile, path)
            else:
                return archivecontents.getvalue()
        finally:
            if tempzipfile is not None and os.path.exists(tempzipfile):
                os.remove(tempzipfile)
            try:
                archivecontents.close()
            except:
                pass

    ###########################################################################

    def make_indexer(self):
        """Get an indexing object for this project.

        Since we do not want to keep the indexing databases open for the
        lifetime of the TranslationProject (it is cached!), it may NOT be
        part of the Project object, but should be used via a short living
        local variable.
        """
        logging.debug(u"Loading indexer for %s", self.pootle_path)
        indexdir = os.path.join(self.abs_real_path, self.index_directory)
        from translate.search import indexing
        indexer = indexing.get_indexer(indexdir)
        indexer.set_field_analyzers({
            "pofilename": indexer.ANALYZER_EXACT,
            "pomtime": indexer.ANALYZER_EXACT,
            "dbid": indexer.ANALYZER_EXACT,
        })

        return indexer

    def init_index(self, indexer):
        """Initializes the search index."""
        #FIXME: stop relying on pomtime so virtual files can be searchable?
        try:
            indexer.begin_transaction()
            for store in self.stores.iterator():
                try:
                    self.update_index(indexer, store)
                except OSError:
                    # Broken link or permission problem?
                    logging.exception("Error indexing %s", store)
            indexer.commit_transaction()
            indexer.flush(optimize=True)
        except Exception:
            logging.exception(u"Error opening indexer for %s", self)
            try:
                indexer.cancel_transaction()
            except:
                pass

    def update_index(self, indexer, store, unitid=None):
        """Updates the index with the contents of store (limit to
        ``unitid`` if given).

        There are two reasons for calling this function:

            1. Creating a new instance of :cls:`TranslationProject`
               (see :meth:`TranslationProject.init_index`)
               -> Check if the index is up-to-date / rebuild the index if
               necessary
            2. Translating a unit via the web interface
               -> (re)index only the specified unit(s)

        The argument ``unitid`` should be None for 1.

        Known problems:

            1. This function should get called, when the po file changes
               externally.

               WARNING: You have to stop the pootle server before manually
               changing po files, if you want to keep the index database in
               sync.
        """
        #FIXME: leverage file updated signal to check if index needs updating
        if indexer is None:
            return False

        # Check if the pomtime in the index == the latest pomtime
        pomtime = str(hash(store.get_mtime()) ** 2)
        pofilenamequery = indexer.make_query([("pofilename",
                                               store.pootle_path)], True)
        pomtimequery = indexer.make_query([("pomtime", pomtime)], True)
        gooditemsquery = indexer.make_query([pofilenamequery, pomtimequery],
                                            True)
        gooditemsnum = indexer.get_query_result(gooditemsquery) \
                              .get_matches_count()

        # If there is at least one up-to-date indexing item, then the po file
        # was not changed externally -> no need to update the database
        units = None
        if (gooditemsnum > 0) and (not unitid):
            # Nothing to be done
            return
        elif unitid is not None:
            # Update only specific item - usually translation via the web
            # interface. All other items should still be up-to-date (even with
            # an older pomtime).
            # Delete the relevant item from the database
            units = store.units.filter(id=unitid)
            itemsquery = indexer.make_query([("dbid", str(unitid))], False)
            indexer.delete_doc([pofilenamequery, itemsquery])
        else:
            # (item is None)
            # The po file is not indexed - or it was changed externally
            # delete all items of this file
            logging.debug(u"Updating %s indexer for file %s", self.pootle_path,
                    store.pootle_path)
            indexer.delete_doc({"pofilename": store.pootle_path})
            units = store.units

        addlist = []
        for unit in units.iterator():
            doc = {
                "pofilename": store.pootle_path,
                "pomtime": pomtime,
                "dbid": str(unit.id),
            }

            if unit.hasplural():
                orig = "\n".join(unit.source.strings)
                trans = "\n".join(unit.target.strings)
            else:
                orig = unit.source
                trans = unit.target

            doc.update({
                "source": orig,
                "target": trans,
                "notes": unit.getnotes(),
                "locations": unit.getlocations(),
            })
            addlist.append(doc)

        if addlist:
            for add_item in addlist:
                indexer.index_document(add_item)

    ###########################################################################

    def gettermmatcher(self):
        """Returns the terminology matcher."""
        terminology_stores = Store.objects.none()
        mtime = None

        if self.is_terminology_project:
            terminology_stores = self.stores.all()
            mtime = self.get_mtime()
        else:
            # Get global terminology first
            try:
                termproject = TranslationProject.objects.get(
                        language=self.language_id,
                        project__code='terminology',
                )
                mtime = termproject.get_mtime()
                terminology_stores = termproject.stores.all()
            except TranslationProject.DoesNotExist:
                pass

            local_terminology = self.stores.filter(
                    name__startswith='pootle-terminology')
            for store in local_terminology.iterator():
                if mtime is None:
                    mtime = store.get_mtime()
                else:
                    mtime = max(mtime, store.get_mtime())

            terminology_stores = terminology_stores | local_terminology

        if mtime is None:
            return

        if mtime != self.non_db_state.termmatchermtime:
            from translate.search import match
            self.non_db_state.termmatcher = match.terminologymatcher(
                    terminology_stores.iterator(),
            )
            self.non_db_state.termmatchermtime = mtime

        return self.non_db_state.termmatcher


###############################################################################
# Signal handlers                                                             #
###############################################################################

def scan_languages(sender, instance, created=False, raw=False, **kwargs):
    if not created or raw or instance.disabled:
        return

    for language in Language.objects.iterator():
        create_translation_project(language, instance)

post_save.connect(scan_languages, sender=Project)


def scan_projects(sender, instance, created=False, raw=False, **kwargs):
    if not created or raw:
        return

    for project in Project.objects.enabled().iterator():
        create_translation_project(instance, project)

post_save.connect(scan_projects, sender=Language)
