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

from django.utils.translation import ugettext as _
from django import forms

from translate.storage import factory

from pootle_app.views.util import render_to_kid, render_jtoolkit, KidRequestContext
from pootle_app.views.top_stats import gen_top_stats, top_stats_heading
from pootle_app.views.common import navbar_dict, item_dict, search_forms
from pootle_app.goals import Goal
from pootle_app.fs_models import Directory, Search, Store
from pootle_app.url_manip import URL, TranslateDisplayState, PositionState, read_all_state
from pootle_app.permissions import get_matching_permissions, check_permission, PermissionError
from pootle_app.profile import get_profile
from pootle_app.project_tree import scan_translation_project_files

from Pootle.i18n.jtoolkit_i18n import tr_lang
from Pootle import pan_app
from Pootle import pootlefile

class UploadForm(forms.Form):
    file = forms.FileField()
    overwrite = forms.ChoiceField(widget=forms.RadioSelect,
                                  choices=[('checked',  _("Overwrite the current file if it exists")),
                                           ('', _("Merge the file with the current file and turn conflicts into suggestions"))])

    def __init__(self, allow_overwrite, *args, **kwargs):
        super(UploadForm, self).__init__(*args, **kwargs)
        self.allow_overwrite = allow_overwrite
        self.title = _("Upload File")
    
    def as_p(self):
        vars = {'file':    self['file'].as_widget(),
                'upload':  _('Upload')}
        layout = '<div>%(file)s</div><div>%(overwrite)s</div><input type="submit" name="upload" value="%(upload)s" />'
        if self.allow_overwrite:
            vars['overwrite'] = self['overwrite'].as_widget()
            return layout % vars
        else:
            self.initial['overwrite'] = ''
            vars['overwrite'] = self['overwrite'].as_hidden()
            return layout % vars

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

def get_children(request, translation_project, directory, url_state):
    store_url_state = copy.deepcopy(url_state)
    store_url_state['translate_display'] = TranslateDisplayState(initial={'view_mode': 'translate' })
    return [item_dict.make_directory_item(request, child_dir, url_state)
            for child_dir in directory.child_dirs.all()] + \
           [item_dict.make_store_item(request, child_store, store_url_state)
            for child_store in directory.filter_stores(Search(**url_state['search'].as_dict())).all()]

################################################################################

def top_stats(translation_project):
    return gen_top_stats(lambda query: query.filter(translation_project=translation_project))

def get_real_path(translation_project, url):
    """Gets an absolute path on the filesystem that corresponds to the
    @c{url} relative to @c{translation_project}.

    For example, if @c{url} is /af/pootle/foo/bar, then the path
    relative to the translation project directory is foo/bar. Thus, we
    take foo/bar and convert split it into a list ['foo', 'bar']. Then
    we take the filesystem path of the translation project and join
    these components to it. This gives us a filesystem path relative
    to the Pootle project root. Now we simply absolutify this path to
    get a real path on the filesystem."""
    relative_pootle_path = url[len(translation_project.directory.pootle_path):]
    components = relative_pootle_path.split('/')
    real_path = os.path.join(translation_project.real_path, *components)
    return pootlefile.absolute_real_path(real_path)

def get_upload_path(translation_project, directory, local_filename):
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
    dir_path = get_real_path(translation_project, directory.pootle_path)
    return os.path.join(dir_path, local_filename)

def get_local_filename(translation_project, upload_filename):
    base, ext = os.path.splitext(upload_filename)
    return '%s.%s' % (base, translation_project.project.localfiletype)

def unzip_external(request, directory, django_file, overwrite, **kwargs):
    from tempfile import mkdtemp, mkstemp
    tempdir = mkdtemp(prefix='pootle')
    tempzipfd, tempzipname = mkstemp(prefix='pootle', suffix='.zip')

    try:
        os.write(tempzipfd, django_file.read())
        os.close(tempzipfd)
        if subprocess.call(["unzip", tempzipname, "-d", tempdir]):
            raise zipfile.BadZipfile(_("Error while extracting archive"))
        for basedir, dirs, files in os.walk(tempdir):
            for fname in files:
                full_fname = os.path.join(basedir, fname)
                fcontents = open(full_fname, 'rb').read()
                try:
                    upload_file(request, directory, full_fname[len(tempdir)+1:], fcontents, overwrite)
                except ValueError, e:
                    print "error adding %s" % filename, e
    finally:
        # Clean up temporary file and directory used in try-block
        import shutil
        os.unlink(tempzipname)
        shutil.rmtree(tempdir)

def unzip_python(request, directory, django_file, overwrite, **kwargs):
    archive = zipfile.ZipFile(cStringIO.StringIO(django_file.read()), 'r')
    # TODO: find a better way to return errors...
    try:
        for filename in archive.namelist():
            try:
                upload_file(request, directory, filename, archive.read(filename), overwrite)
            except ValueError, e:
                print "error adding %s" % filename, e
    finally:
        archive.close()

def upload_archive(request, directory, django_file, overwrite, **kwargs):
    # First we try to use "unzip" from the system, otherwise fall back to using
    # the slower zipfile module (below)...
    try:
        unzip_external(request, directory, django_file, overwrite, **kwargs)
    except Exception:
        unzip_python(request, directory, django_file, overwrite, **kwargs)

def upload_file(request, directory, filename, file_contents, overwrite, **kwargs):
    local_filename = get_local_filename(request.translation_project, filename)
    upload_path    = get_upload_path(request.translation_project, directory, local_filename)
    upload_base, upload_ext = os.path.splitext(filename)
    local_base,  local_ext  = os.path.splitext(filename)
    if overwrite and upload_ext != local_ext:
        raise ValueError(_("When uploading a file whose file extension differs from the translation project extension, you can only merge, and not overwrite. %s cannot be uploaded.") % filename)
    if os.path.exists(upload_path) and not overwrite:
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

        store = Store.objects.get(pootle_path=directory.pootle_path + local_filename)
        pootlefile.with_store(request.translation_project, store, do_merge)
    else:
        if not (check_permission("administrate", request) or check_permission("overwrite", request)):
            if overwrite:
                raise PermissionError(_("You do not have rights to overwrite files here"))
            elif not os.path.exists(upload_path):
                raise PermissionError(_("You do not have rights to upload new files here"))
        if not os.path.exists(upload_path):
            os.makedirs(upload_path)
        outfile = open(upload_path, "wb")
        try:
            outfile.write(file_contents)
        finally:
            outfile.close()

def process_upload(request, directory, upload_form, **kwargs):
    django_file = request.FILES['file']
    overwrite   = upload_form['overwrite'].data == 'checked'
    if django_file.name.endswith('.zip'):
        upload_archive(request, directory, django_file, overwrite, **kwargs)
    else:
        upload_file(request, directory, django_file.name, django_file.read(), overwrite, **kwargs)
    scan_translation_project_files(request.translation_project)

post_table = {
    'upload': process_upload
}

def process_post(request, directory, **kwargs):
    for key in request.POST:
        if key in post_table:
            post_table[key](request, directory, **kwargs)

def view(request, translation_project, directory):
    project  = translation_project.project
    language = translation_project.language

    if check_permission('administrate', request):
        upload_form = UploadForm(check_permission('overwrite', request),
                                 data=request.POST,
                                 initial={'file': '', 'overwrite': ''})
    else:
        upload_form = None
    assign_form = None
    goal_form = None

    process_post(request, directory, upload_form=upload_form)

    request.permissions = get_matching_permissions(get_profile(request.user), translation_project.directory)
    url_state = read_all_state(request.GET)
    url_state['position'] = PositionState()
    template_vars = {
        'pagetitle':             _('%s: Project %s, Language %s') % \
            (pan_app.get_title(), project.fullname, tr_lang(language.fullname)),
        'project':               {"code": project.code,  "name": project.fullname},
        'language':              {"code": language.code, "name": tr_lang(language.fullname)},
        'search':                search_forms.get_search_form(request),
        'children':              get_children(request, translation_project, directory, url_state),
        'navitems':              [navbar_dict.make_directory_navbar_dict(request, directory, url_state)],
        'stats_headings':        get_stats_headings(),
        'editing':               url_state['translate_display'].editing,
        'untranslated_text':     _("%s untranslated words"),
        'fuzzy_text':            _("%s fuzzy words"),
        'complete':              _("Complete"),
        'topstats':              top_stats(translation_project),
        'topstatsheading':       top_stats_heading(),
        'upload':                upload_form,
        'assign':                assign_form,
        'goals':                 goal_form,
        }

    return render_to_kid("fileindex.html", KidRequestContext(request, template_vars))
