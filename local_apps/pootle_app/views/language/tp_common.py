#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009 Zuza Software Foundation
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
import StringIO
import subprocess
import zipfile

from django import forms
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _

from translate.storage import factory, versioncontrol

from pootle_app.lib import view_handler
from pootle_app.project_tree import scan_translation_project_files
from pootle_app.models.permissions import check_permission, PermissionError
from pootle_app.models.signals import post_file_upload
from pootle_app.views.language import item_dict
from pootle_app.views.language import search_forms
from pootle_store.models import Store
from pootle_store.util import absolute_real_path, relative_real_path

def get_children(request, translation_project, directory, links_required=None):
    search = search_forms.search_from_request(request)
    return [item_dict.make_directory_item(request, child_dir, links_required=links_required)
            for child_dir in directory.child_dirs.all()] + \
           [item_dict.make_store_item(request, child_store, links_required=links_required)
            for child_store in directory.filter_stores(search).all()]

def unix_to_host_path(p):
    return os.sep.join(p.split('/'))

def host_to_unix_path(p):
    return '/'.join(p.split(os.sep))

def get_upload_path(translation_project, relative_root_dir, local_filename):
    """gets the path of a translation file being uploaded securely,
    creating directories as neccessary"""
    if os.path.basename(local_filename) != local_filename or local_filename.startswith("."):
        raise ValueError("invalid/insecure file name: %s" % local_filename)
    # XXX: Leakage of the project layout information outside of
    # project_tree.py! The rest of Pootle shouldn't have to care
    # whether something is GNU-style or not.
    if translation_project.file_style == "gnu" and not translation_project.is_template_project:
        if local_filename != translation_project.language.code:
            raise ValueError("invalid GNU-style file name %s: must match '%s.%s' or '%s[_-][A-Z]{2,3}.%s'" %
                             (local_filename, translation_project.language.code,
                              translation_project.project.localfiletype,
                              translation_project.language.code, translation_project.project.localfiletype))
    dir_path = os.path.join(translation_project.real_path, unix_to_host_path(relative_root_dir))
    return relative_real_path(os.path.join(dir_path, local_filename))

def get_local_filename(translation_project, upload_filename):
    base, ext = os.path.splitext(upload_filename)
    new_ext = translation_project.project.localfiletype
    if new_ext == 'po' and translation_project.is_template_project:
        new_ext = 'pot'
    return '%s.%s' % (base, new_ext)

def unzip_external(request, relative_root_dir, django_file, overwrite):
    from tempfile import mkdtemp, mkstemp
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
        for basedir, dirs, files in os.walk(tempdir):
            for fname in files:
                # Read the contents of a file...
                fcontents = open(os.path.join(basedir, fname), 'rb').read()
                # Get the filesystem path relative to the temporary directory
                relative_host_dir = basedir[len(tempdir)+len(os.sep):]
                # Construct a full UNIX path relative to the current
                # translation project URL by attaching a UNIXified
                # 'relative_host_dir' to the root relative path
                # (i.e. the path from which the user is uploading the
                # ZIP file.
                sub_relative_root_dir = os.path.join(relative_root_dir, host_to_unix_path(relative_host_dir))
                try:
                    upload_file(request, sub_relative_root_dir, fname, fcontents, overwrite)
                except ValueError, e:
                    logging.error("error adding %s\t%s", fname, e)
    finally:
        # Clean up temporary file and directory used in try-block
        import shutil
        os.unlink(tempzipname)
        shutil.rmtree(tempdir)

def unzip_python(request, relative_root_dir, django_file, overwrite):
    django_file.seek(0)
    archive = zipfile.ZipFile(django_file, 'r')
    # TODO: find a better way to return errors...
    try:
        for filename in archive.namelist():
            try:
                if filename[-1] != '/':
                    sub_relative_root_dir = os.path.join(relative_root_dir, os.path.dirname(filename))
                    newfile = StringIO.StringIO(archive.read(filename))
                    newfile.name = os.path.basename(filename)
                    upload_file(request, sub_relative_root_dir, newfile, overwrite)
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
    _local_base,  local_ext  = os.path.splitext(upload_path)
    # If the extension of the uploaded file matches the extension
    # used in this translation project, then we simply write the
    # file to the disc.
    if upload_ext == local_ext:
        outfile = open(absolute_real_path(upload_path), "wb")
        try:
            outfile.write(django_file.read())
        finally:
            outfile.close()
    else:
        # If the extension of the uploaded file does not match the
        # extension of the current translation project, we create
        # an empty file (with the right extension)...
        empty_store = factory.getobject(absolute_real_path(upload_path))
        # And save it...
        empty_store.save()
        scan_translation_project_files(request.translation_project)
        # Then we open this newly created file and merge the
        # uploaded file into it.
        store = Store.objects.get(file=upload_path)
        newstore = factory.getobject(django_file)
        #FIXME: maybe there is a faster way to do this?
        store.mergefile(newstore, request.user.username, allownewstrings=True, suggestions=False, notranslate=False, obsoletemissing=False)
    
def upload_file(request, relative_root_dir, django_file, overwrite):
    local_filename = get_local_filename(request.translation_project, django_file.name)
    # The full filesystem path to 'local_filename'
    upload_path    = get_upload_path(request.translation_project, relative_root_dir, local_filename)

    file_exists = os.path.exists(absolute_real_path(upload_path))
    if file_exists and overwrite == 'overwrite' and not check_permission('overwrite', request):
        raise PermissionError(_("You do not have rights to overwrite files here."))
    if not file_exists and not check_permission('administrate', request):
        raise PermissionError(_("You do not have rights to upload new files here"))
    if overwrite == 'merge' and not check_permission('translate', request):
        raise PermissionError(_("You do not have rights to upload files here"))
    if overwrite == 'suggest' and not check_permission('suggest', request):
        raise PermissionError(_("You do not have rights to upload files here"))
    
    if not file_exists or overwrite == 'overwrite':
        overwrite_file(request, relative_root_dir, django_file, upload_path)
        return
    
    store = Store.objects.get(file=upload_path)
    # for some reason factory checks explicitly for file existance and
    # if file is open, which makes it impossible to work with Django's
    # in memory uploads.
    #
    # settings _closed to False should work around this
    #FIXME: hackish, does this have any undesirable side effect?
    django_file._closed = False
    newstore = factory.getobject(django_file)
    
    #FIXME: are we sure this is what we want to do? shouldn't we
    # diffrentiate between structure changing uploads and mere
    # pretranslate uploads?
    suggestions = overwrite == 'merge'
    notranslate = overwrite == 'suggest'
    allownewstrings = check_permission('overwrite', request) or check_permission('administrate', request) or check_permission('commit', request)
    obsoletemissing = allownewstrings and overwrite == 'merge'
    store.mergefile(newstore, request.user.username, suggestions=suggestions, notranslate=notranslate,
                    allownewstrings=allownewstrings, obsoletemissing=obsoletemissing)

class UpdateHandler(view_handler.Handler):
    actions = [('do_update', _('Update all from version control'))]

    class Form(forms.Form):
        pass

    def do_update(self, request, translation_project, directory):
        translation_project.update_from_version_control()
        return {}

    @classmethod
    def must_display(self, request, *args, **kwargs):
        return check_permission('commit', request) and \
            versioncontrol.hasversioning(request.translation_project.abs_real_path)

class UploadHandler(view_handler.Handler):
    actions = [('do_upload', _('Upload'))]

    class Form(forms.Form):
        file = forms.FileField(required=False)
        overwrite = forms.ChoiceField(widget=forms.RadioSelect, label='', 
                                      choices=[('merge', _("Merge the file with the current file and turn conflicts into suggestions")),
                                               ('overwrite',  _("Overwrite the current file if it exists")),
                                               ('suggest', _("Add all new translations as suggestions"))])
    @classmethod
    def must_display(self, request, *args, **kwargs):
        return check_permission('translate', request)

    def __init__(self, data, request, *args, **kwargs):
        super(UploadHandler, self).__init__(data, request, *args, **kwargs)
        self.form.allow_overwrite = check_permission('overwrite', request)
        self.form.title = _("Upload File")

    def do_upload(self, request, translation_project, directory):
        if self.form.is_valid():
            django_file = request.FILES['file']
            overwrite = self.form.cleaned_data['overwrite']
            scan_translation_project_files(translation_project)
            oldstats = translation_project.getquickstats()
            # The URL relative to the URL of the translation project. Thus, if
            # directory.pootle_path == /af/pootle/foo/bar, then
            # relative_root_dir == foo/bar.
            relative_root_dir = directory.pootle_path[len(translation_project.directory.pootle_path):]
            if django_file.name.endswith('.zip'):
                archive = True
                upload_archive(request, relative_root_dir, django_file, overwrite)
            else:
                archive = False
                upload_file(request, relative_root_dir, django_file, overwrite)
            scan_translation_project_files(translation_project)
            newstats = translation_project.getquickstats()
            post_file_upload.send(sender=translation_project, user=request.user, oldstats=oldstats,
                                  newstats=newstats, archive=archive)
        return {}
