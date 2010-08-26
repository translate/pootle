#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008-2009 Zuza Software Foundation
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

import os
import logging
import StringIO
import subprocess
import zipfile
import datetime
from tempfile import mkdtemp, mkstemp

from django.shortcuts import get_object_or_404
from django.conf import settings
from django.core.cache import cache
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import PermissionDenied
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.forms.models import BaseModelFormSet
from django import forms

from translate.storage import factory, versioncontrol

from pootle_misc.baseurl import redirect
from pootle_app.models.permissions import get_matching_permissions, check_permission
from pootle_app.models.signals import post_file_upload
from pootle_app.models             import Directory
from pootle_app.lib import view_handler
from pootle_app.views.top_stats import gentopstats_translation_project
from pootle_app.views.base import BaseView
from pootle_app.views.language import navbar_dict, dispatch, item_dict
from pootle_app.views.language.view import get_stats_headings
from pootle_app.views.admin import util
from pootle_app.views.admin.permissions import admin_permissions
from pootle_app.views.language.view import get_translation_project, set_request_context
from pootle_app.project_tree import ensure_target_dir_exists

from pootle_store.models import Store, Unit
from pootle_store.util import absolute_real_path, relative_real_path
from pootle_store.filetypes import factory_classes
from pootle_store.views import translate_page
from pootle_statistics.models import Submission
from pootle_profile.models import get_profile

class TPTranslateView(BaseView):
    def GET(self, template_vars, request, translation_project, directory):
        template_vars = super(TPTranslateView, self).GET(template_vars, request)
        request.permissions = get_matching_permissions(get_profile(request.user), translation_project.directory)
        project  = translation_project.project
        language = translation_project.language

        template_vars.update({
            'translation_project': translation_project,
            'project': project,
            'language': language,
            'directory': directory,
            'children': get_children(request, translation_project, directory, links_required='translate'),
            'navitems': [navbar_dict.make_directory_navbar_dict(request, directory, links_required='translate')],
            'feed_path': directory.pootle_path[1:],
            'topstats': gentopstats_translation_project(translation_project),
            })
        return template_vars

@get_translation_project
@set_request_context
def tp_translate(request, translation_project, dir_path):
    request.permissions = get_matching_permissions(get_profile(request.user),
                                                   translation_project.directory)
    if not check_permission("view", request):
        raise PermissionDenied(_("You do not have rights to access translation mode."))

    directory = get_object_or_404(Directory, pootle_path=translation_project.directory.pootle_path + dir_path)

    view_obj = TPTranslateView(forms=dict(upload=UploadHandler,
                                          update=UpdateHandler))
    return render_to_response("translation_project/tp_translate.html",
                         view_obj(request, translation_project, directory),
                              context_instance=RequestContext(request))


class TPReviewView(BaseView):
    def GET(self, template_vars, request, translation_project, directory):
        template_vars = super(TPReviewView, self).GET(template_vars, request)
        request.permissions = get_matching_permissions(get_profile(request.user), translation_project.directory)
        project  = translation_project.project
        language = translation_project.language

        template_vars.update({
            'translation_project': translation_project,
            'project': project,
            'language': language,
            'directory': directory,
            'children': get_children(request, translation_project, directory, links_required='review'),
            'navitems': [navbar_dict.make_directory_navbar_dict(request, directory, links_required='review')],
            'topstats': gentopstats_translation_project(translation_project),
            'feed_path': directory.pootle_path[1:],
            })
        return template_vars

@get_translation_project
@set_request_context
def tp_review(request, translation_project, dir_path):
    request.permissions = get_matching_permissions(get_profile(request.user),
                                                   translation_project.directory)
    if not check_permission("view", request):
        raise PermissionDenied(_("You do not have rights to access review mode."))

    directory = get_object_or_404(Directory, pootle_path=translation_project.directory.pootle_path + dir_path)
    view_obj = TPReviewView({})
    return render_to_response("translation_project/tp_review.html",
                              view_obj(request, translation_project, directory),
                              context_instance=RequestContext(request))

@get_translation_project
@set_request_context
@util.has_permission('administrate')
def tp_admin_permissions(request, translation_project):
    language               = translation_project.language
    project                = translation_project.project

    template_vars = {
        'translation_project': translation_project,
        "project": project,
        "language": language,
        "directory": translation_project.directory,
        "navitems": [navbar_dict.make_directory_navbar_dict(request, translation_project.directory)],
        "feed_path": translation_project.pootle_path[1:],
    }
    return admin_permissions(request, translation_project.directory, "translation_project/tp_admin_permissions.html",
                             template_vars)


class StoreFormset(BaseModelFormSet):
    def save_existing_objects(self, commit=True):
        result = super(StoreFormset, self).save_existing_objects(commit)
        for store in self.deleted_objects:
            #hackish: we disabled deleting files when field is
            # deleted except for when value is being overwritten, but
            # this form is the only place in pootle where actual file
            # system files should be deleted
            if store.file:
                store.file.storage.delete(store.file.name)
        return result

@get_translation_project
@set_request_context
@util.has_permission('administrate')
def tp_admin_files(request, translation_project):
    queryset = translation_project.stores.all()
    if 'template_update' in request.POST:
        translation_project.update_from_templates()
        request.POST = {}

    if 'scan_files' in request.POST:
        translation_project.scan_files()
        for store in translation_project.stores.exclude(file='').iterator():
            store.sync(update_translation=True)
            store.update(update_structure=True, update_translation=True, conservative=False)
        request.POST = {}

    model_args = {
        'title': _("Files"),
        'submitname': "changestores",
        'formid': "stores",
        'navitems': [navbar_dict.make_directory_navbar_dict(request, translation_project.directory)],
        'feed_path': translation_project.directory.pootle_path[1:],
        'translation_project': translation_project,
        'language': translation_project.language,
        'project': translation_project.project,
        'directory': translation_project.directory,
        }
    link = lambda instance: '<a href="%s/translate">%s</a>' % (
        instance.pootle_path, instance.pootle_path[len(translation_project.pootle_path):])

    return util.edit(request, 'translation_project/tp_admin_files.html', Store, model_args,
                     link, linkfield='pootle_path', queryset=queryset,
                     formset=StoreFormset, can_delete=True, extra=0)

class ProjectIndexView(BaseView):
    def GET(self, template_vars, request, translation_project, directory):
        template_vars = super(ProjectIndexView, self).GET(template_vars, request)
        request.permissions = get_matching_permissions(get_profile(request.user), translation_project.directory)
        state    = dispatch.ProjectIndexState(request.GET)
        project  = translation_project.project
        language = translation_project.language

        template_vars.update({
            'translation_project': translation_project,
            'project': project,
            'language': language,
            'directory': directory,
            'children': get_children(request, translation_project, directory),
            'navitems': [navbar_dict.make_directory_navbar_dict(request, directory)],
            'stats_headings': get_stats_headings(),
            'editing': state.editing,
            'topstats': gentopstats_translation_project(translation_project),
            'feed_path': directory.pootle_path[1:],
            })
        return template_vars

@get_translation_project
@set_request_context
def tp_overview(request, translation_project, dir_path):
    request.permissions = get_matching_permissions(get_profile(request.user),
                                                   translation_project.directory)
    if not check_permission("view", request):
        raise PermissionDenied(_("You do not have rights to access this translation project."))
    directory = get_object_or_404(Directory, pootle_path=translation_project.directory.pootle_path + dir_path)
    view_obj = ProjectIndexView(forms=dict(upload=UploadHandler,
                                           update=UpdateHandler))
    return render_to_response("translation_project/tp_overview.html",
                              view_obj(request, translation_project, directory),
                              context_instance=RequestContext(request))

@get_translation_project
@set_request_context
def export_zip(request, translation_project, file_path):
    if not check_permission("archive", request):
        raise PermissionDenied(_('You do not have the right to create ZIP archives.'))
    translation_project.sync()
    pootle_path = translation_project.pootle_path + (file_path or '')

    archivename = '%s-%s' % (translation_project.project.code, translation_project.language.code)
    if file_path.endswith('/'):
        file_path = file_path[:-1]

    if file_path:
        archivename += '-' + file_path.replace('/', '-')
    archivename += '.zip'
    export_path = os.path.join('POOTLE_EXPORT', translation_project.real_path, archivename)
    abs_export_path = absolute_real_path(export_path)

    key = "%s:export_zip" % pootle_path
    last_export = cache.get(key)
    if not (last_export and last_export == translation_project.get_mtime() and os.path.isfile(abs_export_path)):
        ensure_target_dir_exists(abs_export_path)

        stores = Store.objects.filter(pootle_path__startswith=pootle_path).exclude(file='')
        translation_project.get_archive(stores, abs_export_path)
        cache.set(key, translation_project.get_mtime(), settings.OBJECT_CACHE_TIMEOUT)
    return redirect('/export/' + export_path)

def get_children(request, translation_project, directory, links_required=None):
    return [item_dict.make_directory_item(request, child_dir, links_required=links_required)
            for child_dir in directory.child_dirs.iterator()] + \
           [item_dict.make_store_item(request, child_store, links_required=links_required)
            for child_store in directory.child_stores.iterator()]

def unix_to_host_path(p):
    return os.sep.join(p.split('/'))

def host_to_unix_path(p):
    return '/'.join(p.split(os.sep))

def get_upload_path(translation_project, relative_root_dir, local_filename):
    """gets the path of a translation file being uploaded securely,
    creating directories as neccessary"""
    dir_path = os.path.join(translation_project.real_path, unix_to_host_path(relative_root_dir))
    return relative_real_path(os.path.join(dir_path, local_filename))

def get_local_filename(translation_project, upload_filename):
    base, ext = os.path.splitext(upload_filename)
    new_ext = translation_project.project.localfiletype
    if new_ext == 'po' and translation_project.is_template_project:
        new_ext = 'pot'
    local_filename =  '%s.%s' % (base, new_ext)

    # check if name is valid

    if os.path.basename(local_filename) != local_filename or local_filename.startswith("."):
        raise ValueError(_("Invalid/insecure file name: %s", local_filename))
    # XXX: Leakage of the project layout information outside of
    # project_tree.py! The rest of Pootle shouldn't have to care
    # whether something is GNU-style or not.
    if translation_project.file_style == "gnu" and not translation_project.is_template_project:
        if os.path.splitext(local_filename)[0] != translation_project.language.code:
            raise ValueError(_("Invalid GNU-style file name: %(local_filename)s. It must match '%(langcode)s.%(filetype)s'.",
                             {'local_filename': local_filename,
                              'langcode': translation_project.language.code,
                              'filetype': translation_project.project.localfiletype,
                              }))
    return local_filename

def unzip_external(request, directory, django_file, overwrite):
    # Make a temporary directory to hold a zip file and its unzipped contents
    tempdir = mkdtemp(prefix='pootle')
    # Make a temporary file to hold the zip file
    tempzipfd, tempzipname = mkstemp(prefix='pootle', suffix='.zip')
    try:
        # Dump the uploaded file to the temporary file
        try:
            os.write(tempzipfd, django_file.read())
        finally:
            os.close(tempzipfd)
        # Unzip the temporary zip file
        if subprocess.call(["unzip", tempzipname, "-d", tempdir]):
            raise zipfile.BadZipfile(_("Error while extracting archive"))
        # Enumerate the temporary directory...
        maybe_skip = True
        prefix = tempdir
        for basedir, dirs, files in os.walk(tempdir):
            if maybe_skip and not files and len(dirs) == 1:
                try:
                    directory.child_dirs.get(name=dirs[0])
                    maybe_skip = False
                except Directory.DoesNotExist:
                    prefix = os.path.join(basedir, dirs[0])
                    continue
            else:
                maybe_skip = False

            for fname in files:
                # Read the contents of a file...
                newfile = StringIO.StringIO(open(os.path.join(basedir, fname), 'rb').read())
                newfile.name = os.path.basename(fname)
                # Get the filesystem path relative to the temporary directory
                subdir = host_to_unix_path(basedir[len(prefix)+len(os.sep):])
                if subdir:
                    target_dir = directory.get_or_make_subdir(subdir)
                else:
                    target_dir = directory
                # Construct a full UNIX path relative to the current
                # translation project URL by attaching a UNIXified
                # 'relative_host_dir' to the root relative path
                # (i.e. the path from which the user is uploading the
                # ZIP file.
                try:
                    upload_file(request, target_dir, newfile, overwrite)
                except ValueError, e:
                    logging.error("error adding %s\t%s", fname, e)
    finally:
        # Clean up temporary file and directory used in try-block
        import shutil
        os.unlink(tempzipname)
        shutil.rmtree(tempdir)

def unzip_python(request, directory, django_file, overwrite):
    django_file.seek(0)
    archive = zipfile.ZipFile(django_file, 'r')
    # TODO: find a better way to return errors...
    try:
        prefix = ''
        maybe_skip = True
        for filename in archive.namelist():
            try:
                if filename[-1] == '/':
                    if maybe_skip:
                        try:
                            directory.child_dirs.get(name=filename[:-1])
                            maybe_skip = False
                        except Directory.DoesNotExist:
                            prefix = filename
                else:
                    maybe_skip = False
                    subdir = host_to_unix_path(os.path.dirname(filename[len(prefix):]))
                    if subdir:
                        target_dir = directory.get_or_make_subdir(subdir)
                    else:
                        target_dir = directory
                    newfile = StringIO.StringIO(archive.read(filename))
                    newfile.name = os.path.basename(filename)
                    upload_file(request, target_dir, newfile, overwrite)
            except ValueError, e:
                logging.error("error adding %s\t%s", filename, e)
    finally:
        archive.close()

def upload_archive(request, directory, django_file, overwrite):
    # First we try to use "unzip" from the system, otherwise fall back to using
    # the slower zipfile module
    try:
        unzip_external(request, directory, django_file, overwrite)
    except:
        unzip_python(request, directory, django_file, overwrite)

def overwrite_file(request, relative_root_dir, django_file, upload_path):
    """overwrite with uploaded file"""
    upload_dir = os.path.dirname(absolute_real_path(upload_path))
    # Ensure that there is a directory into which we can dump the
    # uploaded file.
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)

    # Get the file extensions of the uploaded filename and the
    # current translation project
    _upload_base, upload_ext = os.path.splitext(django_file.name)
    _local_base, local_ext = os.path.splitext(upload_path)
    # If the extension of the uploaded file matches the extension
    # used in this translation project, then we simply write the
    # file to the disc.
    if upload_ext == local_ext:
        outfile = open(absolute_real_path(upload_path), "wb")
        try:
            outfile.write(django_file.read())
        finally:
            outfile.close()
            try:
                #FIXME: we need a way to delay reparsing
                store = Store.objects.get(file=upload_path)
                store.update(update_structure=True, update_translation=True, conservative=False)
            except Store.DoesNotExist:
                # newfile, delay parsing
                pass
    else:
        newstore = factory.getobject(django_file, classes=factory_classes)
        if not newstore.units:
            return

        # If the extension of the uploaded file does not match the
        # extension of the current translation project, we create
        # an empty file (with the right extension)...
        empty_store = factory.getobject(absolute_real_path(upload_path), classes=factory_classes)
        # And save it...
        empty_store.save()
        request.translation_project.scan_files()
        # Then we open this newly created file and merge the
        # uploaded file into it.
        store = Store.objects.get(file=upload_path)
        #FIXME: maybe there is a faster way to do this?
        store.mergefile(newstore, get_profile(request.user), allownewstrings=True, suggestions=False, notranslate=False, obsoletemissing=False)

def upload_file(request, directory, django_file, overwrite, store=None):
    translation_project = request.translation_project
    relative_root_dir = directory.pootle_path[len(translation_project.pootle_path):]
    # for some reason factory checks explicitly for file existance and
    # if file is open, which makes it difficult to work with Django's
    # in memory uploads.
    #
    # setting _closed to False should work around this
    #FIXME: hackish, does this have any undesirable side effect?
    if getattr(django_file, '_closed', None) is None:
        try:
            django_file._closed = False
        except AttributeError:
            pass
    # factory also checks for _mode
    if getattr(django_file, '_mode', None) is None:
        try:
            django_file._mode = 1
        except AttributeError:
            pass
    # mode is an attribute not a property in Django 1.1
    if getattr(django_file, 'mode', None) is None:
        django_file.mode = 1

    local_filename = get_local_filename(translation_project, django_file.name)
    if store and store.file:
        pootle_path = store.pootle_path
        upload_path = store.real_path
    else:
        pootle_path = directory.pootle_path + local_filename
        # The full filesystem path to 'local_filename'
        upload_path    = get_upload_path(translation_project, relative_root_dir, local_filename)
        try:
            store = translation_project.stores.get(pootle_path=pootle_path)
        except Store.DoesNotExist:
            store = None

    if store is not None and overwrite == 'overwrite' and not check_permission('overwrite', request):
        raise PermissionDenied(_("You do not have rights to overwrite files here."))
    if store is None and not check_permission('administrate', request):
        raise PermissionDenied(_("You do not have rights to upload new files here."))
    if overwrite == 'merge' and not check_permission('translate', request):
        raise PermissionDenied(_("You do not have rights to upload files here."))
    if overwrite == 'suggest' and not check_permission('suggest', request):
        raise PermissionDenied(_("You do not have rights to upload files here."))

    if store is None or (overwrite == 'overwrite' and store.file != ""):
        overwrite_file(request, relative_root_dir, django_file, upload_path)
        return

    if store.file and store.file.read() == django_file.read():
        logging.debug("identical file uploaded to %s, not merging", store.pootle_path)
        return

    django_file.seek(0)
    newstore = factory.getobject(django_file, classes=factory_classes)

    #FIXME: are we sure this is what we want to do? shouldn't we
    # diffrentiate between structure changing uploads and mere
    # pretranslate uploads?
    suggestions = overwrite == 'merge'
    notranslate = overwrite == 'suggest'
    #allownewstrings = check_permission('overwrite', request) or check_permission('administrate', request) or check_permission('commit', request)
    #obsoletemissing = allownewstrings and overwrite == 'merge'
    store.mergefile(newstore, get_profile(request.user), suggestions=suggestions, notranslate=notranslate,
                    allownewstrings=False, obsoletemissing=False)

class UpdateHandler(view_handler.Handler):
    actions = [('do_update', _('Update all from version control'))]

    class Form(forms.Form):
        pass

    def do_update(self, request, translation_project, directory):
        translation_project.update_project(request)
        return {}

    @classmethod
    def must_display(cls, request, *args, **kwargs):
        return check_permission('commit', request) and \
            versioncontrol.hasversioning(request.translation_project.abs_real_path)

class UploadHandler(view_handler.Handler):
    actions = [('do_upload', _('Upload'))]

    @classmethod
    def must_display(cls, request, *args, **kwargs):
        return check_permission('translate', request)

    def __init__(self, request, data=None, files=None):
        choices = [('merge', _("Merge the file with the current file and turn conflicts into suggestions")),
                   ('suggest', _("Add all new translations as suggestions"))]
        if check_permission('overwrite', request):
            choices.insert(0, ('overwrite', _("Overwrite the current file if it exists")))

        translation_project = request.translation_project

        class StoreFormField(forms.ModelChoiceField):
            def label_from_instance(self, instance):
                return _(instance.pootle_path[len(translation_project.pootle_path):])

        class DirectoryFormField(forms.ModelChoiceField):
            def label_from_instance(self, instance):
                return _(instance.pootle_path[len(translation_project.pootle_path):])

        class UploadForm(forms.Form):
            file = forms.FileField(required=True, label=_('File'))
            overwrite = forms.ChoiceField(required=True, widget=forms.RadioSelect,
                                          label='', choices=choices, initial='merge')
            upload_to = StoreFormField(required=False, label=_('Upload to'),
                                       queryset=translation_project.stores.all(),
                                       help_text=_("Optionally select the file you want to merge with. If not specified, the uploaded file's name is used."))
            upload_to_dir = DirectoryFormField(required=False, label=_('Upload to'),
                              queryset=Directory.objects.filter(pootle_path__startswith=translation_project.pootle_path).exclude(pk=translation_project.directory.pk),
                              help_text=_("Optionally select the file you want to merge with. If not specified, the uploaded file's name is used."))


        self.Form = UploadForm
        super(UploadHandler, self).__init__(request, data, files)
        self.form.allow_overwrite = check_permission('overwrite', request)
        self.form.title = _("Upload File")

    def do_upload(self, request, translation_project, directory):
        if self.form.is_valid() and 'file' in request.FILES:
            django_file = self.form.cleaned_data['file']
            overwrite = self.form.cleaned_data['overwrite']
            upload_to = self.form.cleaned_data['upload_to']
            upload_to_dir = self.form.cleaned_data['upload_to_dir']
            translation_project.scan_files()
            oldstats = translation_project.getquickstats()
            # The URL relative to the URL of the translation project. Thus, if
            # directory.pootle_path == /af/pootle/foo/bar, then
            # relative_root_dir == foo/bar.
            if django_file.name.endswith('.zip'):
                archive = True
                target_directory = upload_to_dir or directory
                upload_archive(request, target_directory, django_file, overwrite)
            else:
                archive = False
                upload_file(request, directory, django_file, overwrite, store=upload_to)
            translation_project.scan_files()
            newstats = translation_project.getquickstats()

            # create a submission, doesn't fix stats but at least
            # shows up in last activity column
            s = Submission(creation_time=datetime.datetime.utcnow(),
                           translation_project=translation_project,
                           submitter=get_profile(request.user))
            s.save()

            post_file_upload.send(sender=translation_project, user=request.user, oldstats=oldstats,
                                  newstats=newstats, archive=archive)
        return {'upload': self}

@get_translation_project
@set_request_context
def translate(request, translation_project):
    units_queryset = Unit.objects.filter(store__translation_project=translation_project)
    return translate_page(request, units_queryset)
