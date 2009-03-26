#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Copyright 2009 Zuza Software Foundation
# 
# This file is part of Pootle.
#
# Pootle is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# Pootle is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Pootle; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

import copy
import os
import zipfile
import subprocess
import cStringIO

from django.utils.translation import ugettext as _
from django import forms

from translate.storage import factory

from pootle_app.views.util import render_to_kid, render_jtoolkit
from pootle_app.views.top_stats import gen_top_stats, top_stats_heading
from pootle_app.views.common import navbar_dict, item_dict, search_forms
from pootle_app.models import Goal, Directory, Store
from pootle_app.models.search import Search
from pootle_app.models.permissions import get_matching_permissions, check_permission, PermissionError
from pootle_app.models.profile import get_profile
from pootle_app.project_tree import scan_translation_project_files
from pootle_app import url_manip
from pootle_app.lib import view_handler
from pootle_app.views.base import BaseView
import dispatch

from Pootle.i18n.jtoolkit_i18n import tr_lang
from Pootle import pan_app
from Pootle import pootlefile



################################################################################

def get_stats_headings():
    """returns a dictionary of localised headings"""
    return {
        "name":                   _("Name"),
        "translated":             _("Translated"),
        "translatedpercentage":   _("Translated percentage"),
        "translatedwords":        _("Translated words"),
        "fuzzy":                  _("Fuzzy"),
        "fuzzypercentage":        _("Fuzzy percentage"),
        "fuzzywords":             _("Fuzzy words"),
        "untranslated":           _("Untranslated"),
        "untranslatedpercentage": _("Untranslated percentage"),
        "untranslatedwords":      _("Untranslated words"),
        "total":                  _("Total"),
        "totalwords":             _("Total words"),
        # l10n: noun. The graphical representation of translation status
        "progress":               _("Progress"),
        "summary":                _("Summary")
        }

################################################################################

def get_children(request, translation_project, directory):
    search = Search.from_request(request)
    return [item_dict.make_directory_item(request, child_dir)
            for child_dir in directory.child_dirs.all()] + \
           [item_dict.make_store_item(request, child_store)
            for child_store in directory.filter_stores(search).all()]

################################################################################

def top_stats(translation_project):
    return gen_top_stats(lambda query: query.filter(translation_project=translation_project))

################################################################################

def unix_to_host_path(p):
    return os.sep.join(p.split('/'))

def host_to_unix_path(p):
    return '/'.join(p.split(os.sep))

def get_upload_path(translation_project, relative_root_dir, local_filename):
    """gets the path of a translation file being uploaded securely,
    creating directories as neccessary"""
    if os.path.basename(local_filename) != local_filename or local_filename.startswith("."):
        raise ValueError("invalid/insecure file name: %s" % localfilename)
    # XXX: Leakage of the project layout information outside of
    # project_tree.py! The rest of Pootle shouldn't have to care
    # whether something is GNU-style or not.
    if translation_project.file_style == "gnu":
        if local_filename != translation_project.language.code:
            raise ValueError("invalid GNU-style file name %s: must match '%s.%s' or '%s[_-][A-Z]{2,3}.%s'" % (localfilename, self.languagecode, self.fileext, self.languagecode, self.fileext))
    dir_path = os.path.join(translation_project.real_path, unix_to_host_path(relative_root_dir))
    return pootlefile.relative_real_path(os.path.join(dir_path, local_filename))

def get_local_filename(translation_project, upload_filename):
    base, ext = os.path.splitext(upload_filename)
    return '%s.%s' % (base, translation_project.project.localfiletype)

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
                    print "error adding %s" % filename, e
    finally:
        # Clean up temporary file and directory used in try-block
        import shutil
        os.unlink(tempzipname)
        shutil.rmtree(tempdir)

def unzip_python(request, relative_root_dir, django_file, overwrite):
    archive = zipfile.ZipFile(cStringIO.StringIO(django_file.read()), 'r')
    # TODO: find a better way to return errors...
    try:
        for filename in archive.namelist():
            try:
                if filename[-1] != '/':
                    sub_relative_root_dir = os.path.join(relative_root_dir, os.path.dirname(filename))
                    basename = os.path.basename(filename)
                    upload_file(request, sub_relative_root_dir, basename, archive.read(filename), overwrite)
            except ValueError, e:
                print "error adding %s" % filename, e
    finally:
        archive.close()

def upload_archive(request, directory, django_file, overwrite):
    # First we try to use "unzip" from the system, otherwise fall back to using
    # the slower zipfile module
    try:
        unzip_external(request, directory, django_file, overwrite)
    except:
        unzip_python(request, directory, django_file, overwrite)

def upload_file(request, relative_root_dir, filename, file_contents, overwrite):
    # Strip the extension off filename and add the extension used in
    # the current translation project to filename to get
    # local_filename. Thus, if filename == 'foo.xlf' and we're in a PO
    # project, then local_filename == 'foo.po'.
    local_filename = get_local_filename(request.translation_project, filename)
    # The full filesystem path to 'local_filename'
    upload_path    = get_upload_path(request.translation_project, relative_root_dir, local_filename)
    if os.path.exists(pootlefile.absolute_real_path(upload_path)) and not overwrite:
        def do_merge(origpofile):
            newfileclass = factory.getclass(filename)
            newfile = newfileclass.parsestring(file_contents)
            if check_permission("administrate", request):
                origpofile.mergefile(newfile, request.user.username)
            elif check_permission("translate", request):
                origpofile.mergefile(newfile, request.user.username, allownewstrings=False)
            elif check_permission("suggest", request):
                origpofile.mergefile(newfile, request.user.username, suggestions=True)
            else:
                raise PermissionError(_("You do not have rights to upload files here"))

        store = Store.objects.get(real_path=upload_path)
        pootlefile.with_store(request.translation_project, store, do_merge)
    else:
        if not (check_permission("administrate", request) or check_permission("overwrite", request)):
            if overwrite:
                raise PermissionError(_("You do not have rights to overwrite files here"))
            elif not os.path.exists(pootlefile.absolute_real_path(upload_path)):
                raise PermissionError(_("You do not have rights to upload new files here"))
        # Get the file extensions of the uploaded filename and the
        # current translation project
        upload_dir = os.path.dirname(pootlefile.absolute_real_path(upload_path))
        # Ensure that there is a directory into which we can dump the
        # uploaded file.
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)
        _upload_base, upload_ext = os.path.splitext(filename)
        _local_base,  local_ext  = os.path.splitext(upload_path)
        # If the extension of the uploaded file matches the extension
        # used in this translation project, then we simply write the
        # file to the disc.
        if upload_ext == local_ext:
            outfile = open(pootlefile.absolute_real_path(upload_path), "wb")
            try:
                outfile.write(file_contents)
            finally:
                outfile.close()
        else:
            def do_merge(new_file):
                uploaded_file_class = factory.getclass(filename)
                uploaded_file = uploaded_file_class.parsestring(file_contents)
                new_file.mergefile(uploaded_file, request.user.username)

            # If the extension of the uploaded file does not match the
            # extension of the current translation project, we create
            # an empty file (with the right extension)...
            empty_store = factory.getobject(pootlefile.absolute_real_path(upload_path))
            # And save it...
            empty_store.save()
            # Then we open this newly created file and merge the
            # uploaded file into it.
            pootlefile.with_pootle_file(request.translation_project, upload_path, do_merge)


class UploadHandler(view_handler.Handler):
    actions = [('do_upload', _('Upload'))]

    class Form(forms.Form):
        file = forms.FileField()
        overwrite = forms.ChoiceField(widget=forms.RadioSelect,
                                      choices=[('checked',  _("Overwrite the current file if it exists")),
                                               ('', _("Merge the file with the current file and turn conflicts into suggestions"))])

        def as_p(self):
            vars = {'file':    self['file'].as_widget(),
                    'upload':  _('Upload')}
            layout = '<div>%(file)s</div><div>%(overwrite)s</div>'
            if self.allow_overwrite:
                vars['overwrite'] = self['overwrite'].as_widget()
                return layout % vars
            else:
                self.initial['overwrite'] = ''
                vars['overwrite'] = self['overwrite'].as_hidden()
                return layout % vars        

    @classmethod
    def must_display(self, request, *args, **kwargs):
        return check_permission('administrate', request)

    def __init__(self, data, request, *args, **kwargs):
        super(UploadHandler, self).__init__(data, request, *args, **kwargs)
        self.form.allow_overwrite = check_permission('overwrite', request)
        self.form.title = _("Upload File")

    def do_upload(self, request, translation_project, directory):
        django_file = request.FILES['file']
        overwrite = self.form['overwrite'].data == 'checked'
        scan_translation_project_files(request.translation_project)
        # The URL relative to the URL of the translation project. Thus, if
        # directory.pootle_path == /af/pootle/foo/bar, then
        # relative_root_dir == foo/bar.
        relative_root_dir = directory.pootle_path[len(request.translation_project.directory.pootle_path):]
        if django_file.name.endswith('.zip'):
            upload_archive(request, relative_root_dir, django_file, overwrite)
        else:
            upload_file(request, relative_root_dir, django_file.name, django_file.read(), overwrite)
        scan_translation_project_files(request.translation_project)
        return {}

class ProjectIndexView(BaseView):
    def GET(self, template_vars, request, translation_project, directory):
        template_vars = super(ProjectIndexView, self).GET(template_vars, request)
        request.permissions = get_matching_permissions(get_profile(request.user), translation_project.directory)
        state    = dispatch.ProjectIndexState(request.GET)
        project  = translation_project.project
        language = translation_project.language

        assign_form = None
        goal_form = None

        template_vars.update({
            'pagetitle':             _('%s: Project %s, Language %s') % \
                (pan_app.get_title(), project.fullname, tr_lang(language.fullname)),
            'project':               {"code": project.code,  "name": project.fullname},
            'language':              {"code": language.code, "name": tr_lang(language.fullname)},
            'search':                search_forms.get_search_form(request),
            'children':              get_children(request, translation_project, directory),
            'navitems':              [navbar_dict.make_directory_navbar_dict(request, directory)],
            'stats_headings':        get_stats_headings(),
            'editing':               state.editing,
            'untranslated_text':     _("%s untranslated words"),
            'fuzzy_text':            _("%s fuzzy words"),
            'complete':              _("Complete"),
            'topstats':              top_stats(translation_project),
            'topstatsheading':       top_stats_heading(),
            'assign':                assign_form,
            'goals':                 goal_form,
            })
        return template_vars

def view(request, translation_project, directory):
    view_obj = ProjectIndexView(forms=dict(upload=UploadHandler))
    return render_to_kid("language/fileindex.html",
                         view_obj(request, translation_project, directory))
