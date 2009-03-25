#!/usr/bin/python
# -*- coding: utf-8 -*-
#  Copyright 2004-2007 Zuza Software Foundation
#
# This file is part of translate.
#
# translate is free software; you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# translate is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# translate; if not, write to the Free Software Foundation, Inc., 59 Temple
# Place, Suite 330, Boston, MA  02111-1307  USA

try:
# ElementTree is part of Python 2.5, so let's try that first
    from xml.etree import ElementTree
except ImportError:
    from elementtree import ElementTree
import os
import sys
import re
import locale
from pootle_app.lib import util
from django.utils.html import escape
from django.conf import settings
from django.utils.translation import ugettext as _
N_ = _
from translate.storage import versioncontrol
from pootle_app.models import Suggestion, Submission, Language, Project, \
    Directory, Goal, TranslationProject
from pootle_app.models.profile import get_profile
from pootle_app.models.permissions import get_matching_permissions
from pootle_app.models import metadata
from pootle_app.language import try_language_code
from pootle_app import project_tree
from Pootle.i18n.jtoolkit_i18n import nlocalize, tr_lang
from Pootle import pan_app, pagelayout, pootlefile

import re

def shortdescription(descr):
    """Returns a short description by removing markup and only
    including up to the first br-tag"""

    stopsign = descr.find('<br')
    if stopsign >= 0:
        descr = descr[:stopsign]
    return re.sub('<[^>]*>', '', descr).strip()


def map_num_contribs(sub, user):
    user.num_contribs = sub.num_contribs
    return user


def users_form_suggestions(sugs):
    """Get the Users associated with the Suggestions. Also assign the
    num_contribs attribute from the Suggestion to the User"""

    return [map_num_contribs(sug, sug.suggester.user) for sug in sugs]


def users_form_submissions(subs):
    """Get the Users associated with the Submissions. Also assign the
    num_contribs attribute from the Submission to the User"""

    return [map_num_contribs(sub, sub.submitter.user) for sub in subs]


def gentopstats(topsugg, topreview, topsub):
    ranklabel = _('Rank')
    namelabel = _('Name')
    topstats = []
    topstats.append({
        'data': users_form_suggestions(topsugg),
        'headerlabel': _('Suggestions'),
        'ranklabel': ranklabel,
        'namelabel': namelabel,
        'vallabel': _('Suggestions'),
        })
    topstats.append({
        'data': users_form_suggestions(topreview),
        'headerlabel': _('Reviews'),
        'ranklabel': ranklabel,
        'namelabel': namelabel,
        'vallabel': _('Reviews'),
        })
    topstats.append({
        'data': users_form_submissions(topsub),
        'headerlabel': _('Submissions'),
        'ranklabel': ranklabel,
        'namelabel': namelabel,
        'vallabel': _('Submissions'),
        })
    return topstats


def limit(query):
    return query[:5]




class PootleIndex(pagelayout.PootlePage):

    """The main page listing projects and languages. It is also reused
    for LanguagesIndex and ProjectsIndex"""

    def __init__(self, request):
        templatename = 'index/index.html'
        description = pan_app.get_description()
        meta_description = shortdescription(description)
        keywords = [
            'Pootle',
            'WordForge',
            'translate',
            'translation',
            'localisation',
            'localization',
            'l10n',
            'traduction',
            'traduire',
            ] + self.getprojectnames()
        languagelink = _('Languages')
        projectlink = _('Projects')
        instancetitle = pan_app.get_title()
        pagetitle = instancetitle
        topsugg = limit(Suggestion.objects.get_top_suggesters())
        topreview = limit(Suggestion.objects.get_top_reviewers())
        topsub = limit(Submission.objects.get_top_submitters())
        topstats = gentopstats(topsugg, topreview, topsub)
        (language_index, project_index) = \
            TranslationProject.get_language_and_project_indices()
        permission_set = get_matching_permissions(get_profile(request.user),
                Directory.objects.root)
        templatevars = {
            'pagetitle': pagetitle,
            'description': description,
            'meta_description': meta_description,
            'keywords': keywords,
            'languagelink': languagelink,
            'languages': self.getlanguages(request, language_index,
                    permission_set),
            'projectlink': projectlink,
            'projects': self.getprojects(request, project_index,
                    permission_set),
            'topstats': topstats,
            'topstatsheading': _('Top Contributors'),
            'instancetitle': instancetitle,
            'translationlegend': self.gettranslationsummarylegendl10n(),
            }
        pagelayout.PootlePage.__init__(self, templatename, templatevars,
                                       request)

    def get_items(self, request, model, latest_changes, item_index, name_func, permission_set):

        def get_percentages(trans, fuzzy):
            try:
                transper = int((100.0 * trans) / total)
                fuzzyper = int((100.0 * fuzzy) / total)
                untransper = (100 - transper) - fuzzyper
            except ZeroDivisionError:
                transper = 100
                fuzzyper = 0
                untransper = 0
            return (transper, fuzzyper, untransper)

        def get_last_action(item, latest_changes):
            if item.code in latest_changes and latest_changes[item.code]\
                 is not None:
                return latest_changes[item.code]
            else:
                return ''

        items = []
        if 'view' not in permission_set:
            return items
        latest_changes = latest_changes()
        for item in [item for item in model.objects.all()
                     if item.code in item_index]:
            trans = 0
            fuzzy = 0
            total = 0
            for translation_project in item_index[item.code]:
                stats = \
                    metadata.quick_stats(translation_project.directory, translation_project.checker)
                trans += stats['translatedsourcewords']
                fuzzy += stats['fuzzysourcewords']
                total += stats['totalsourcewords']
            untrans = (total - trans) - fuzzy
            (transper, fuzzyper, untransper) = get_percentages(trans, fuzzy)
            lastact = get_last_action(item, latest_changes)
            items.append({
                'code': item.code,
                'name': name_func(item.fullname),
                'lastactivity': lastact,
                'trans': trans,
                'fuzzy': fuzzy,
                'untrans': untrans,
                'total': total,
                'transper': transper,
                'fuzzyper': fuzzyper,
                'untransper': untransper,
                })
        items.sort(lambda x, y: locale.strcoll(x['name'], y['name']))
        return items

    def getlanguages(self, request, language_index, permission_set):
        return self.get_items(request, Language, Submission.objects.get_latest_language_changes,
                              language_index, tr_lang, permission_set)

    def getprojects(self, request, project_index, permission_set):
        return self.get_items(request, Project, Submission.objects.get_latest_project_changes,
                              project_index, lambda x: x, permission_set)

    def getprojectnames(self):
        return [proj.fullname for proj in Project.objects.all()]


class UserIndex(pagelayout.PootlePage):
    """home page for a given user"""

    def __init__(self, request):
        self.request = request
        pagetitle = _('User Page for: %s' % request.user.username)
        templatename = 'profile/home.html'
        optionslink = _('Change options')
        adminlink = _('Admin page')
        admintext = _('Administrate')
        quicklinkstitle = _('Quick Links')
        instancetitle = pan_app.get_title()
        quicklinks = self.getquicklinks()
        setoptionstext = \
            _("You need to <a href='options.html'>choose your languages and projects</a>."
              )
        # l10n: %s is the full name of the currently logged in user
        statstitle = _("%s's Statistics" % request.user.first_name)
        statstext = {
            'suggmade': _('Suggestions Made'),
            'suggaccepted': _('Suggestions Accepted'),
            'suggpending': _('Suggestions Pending'),
            'suggrejected': _('Suggestions Rejected'),
            'suggreviewed': _('Suggestions Reviewed'),
            'suggper': _('Suggestion Use Percentage'),
            'submade': _('Submissions Made'),
            }
        templatevars = {
            'pagetitle': pagetitle,
            'optionslink': optionslink,
            'adminlink': adminlink,
            'admintext': admintext,
            'quicklinkstitle': quicklinkstitle,
            'quicklinks': quicklinks,
            'setoptionstext': setoptionstext,
            'instancetitle': instancetitle,
            'statstitle': statstitle,
            'statstext': statstext,
            }
        pagelayout.PootlePage.__init__(self, templatename, templatevars,
                                       request)

    def getquicklinks(self):
        """gets a set of quick links to user's project-languages"""

        quicklinks = []
        user_profile = self.request.user.get_profile()
        # TODO: This can be done MUCH more efficiently with a bit of
        # query forethought.  Why don't we just select all the
        # TranslationProject objects from the database which match the
        # user's Languages and Projects? This should be efficient.
        #
        # But this will only work once we move TranslationProject
        # wholly to the DB (and away from its current brain damaged
        # half-non-db/half-db implementation).
        for language in user_profile.languages.all():
            langlinks = []
            for project in user_profile.projects.all():
                try:
                    projecttitle = project.fullname
                    translation_project = \
                        TranslationProject.objects.get(language=language,
                            project=project)
                    isprojectadmin = 'administrate'\
                         in get_matching_permissions(user_profile,
                            translation_project.directory)
                    langlinks.append({
                        'code': project.code,
                        'name': projecttitle,
                        'isprojectadmin': isprojectadmin,
                        'sep': '<br />',
                        })
                except TranslationProject.DoesNotExist:
                    pass
            if langlinks:
                langlinks[-1]['sep'] = ''
            quicklinks.append({'code': language.code, 'name'
                              : tr_lang(language.fullname), 'projects'
                              : langlinks})
            quicklinks.sort(cmp=locale.strcoll, key=lambda dict: dict['name'])
        return quicklinks


class ProjectsIndex(PootleIndex):
    """the list of languages"""

    def __init__(self, request):
        PootleIndex.__init__(self, request)
        self.templatneame = 'project/projects.html'


class LanguagesIndex(PootleIndex):
    """the list of languages"""

    def __init__(self, request):
        PootleIndex.__init__(self, request)
        self.templatename = 'language/languages.html'


class LanguageIndex(pagelayout.PootleNavPage):
    """The main page for a language, listing all the projects in it"""

    def __init__(self, language, request):
        self.language = language
        self.languagecode = language.code
        self.languagename = language.fullname
        self.initpagestats()
        languageprojects = self.getprojects(request)
        if len(languageprojects) == 0:
            raise projects.Rights404Error
        self.projectcount = len(languageprojects)
        average = self.getpagestats()
        languagestats = nlocalize('%d project, average %d%% translated',
                                  '%d projects, average %d%% translated',
                                  self.projectcount, self.projectcount, average)
        languageinfo = self.getlanguageinfo()
        instancetitle = pan_app.get_title()
        # l10n: The first parameter is the name of the installation
        # l10n: The second parameter is the name of the
        # project/language l10n: This is used as a page title. Most
        # languages won't need to change this
        pagetitle = _('%s: %s' % (instancetitle, tr_lang(self.languagename)))
        templatename = 'language/language.html'
        adminlink = _('Admin')

        def narrow(query):
            return limit(query.filter(translation_project__language__code=self.languagecode))

        topsugg = narrow(Suggestion.objects.get_top_suggesters())
        topreview = narrow(Suggestion.objects.get_top_reviewers())
        topsub = narrow(Submission.objects.get_top_submitters())
        topstats = gentopstats(topsugg, topreview, topsub)
        templatevars = {
            'pagetitle': pagetitle,
            'language': {
                'code': language.code,
                'name': tr_lang(language.fullname),
                'stats': languagestats,
                'info': languageinfo,
                },
            'projects': languageprojects,
            'statsheadings': self.getstatsheadings(),
            'untranslatedtext': _('%s untranslated words'),
            'fuzzytext': _('%s fuzzy words'),
            'complete': _('Complete'),
            'topstats': topstats,
            'topstatsheading': _('Top Contributors'),
            'instancetitle': instancetitle,
            'translationlegend': self.gettranslationsummarylegendl10n(),
            }
        pagelayout.PootleNavPage.__init__(self, templatename, templatevars,
                request, bannerheight=80)

    def getlanguageinfo(self):
        """returns information defined for the language"""

        # specialchars =
        # self.potree.getlanguagespecialchars(self.languagecode)
        nplurals = self.language.nplurals
        pluralequation = self.language.pluralequation
        infoparts = [(_('Language Code'), self.languagecode), (_('Language Name'
                     ), tr_lang(self.languagename)), (_('Number of Plurals'),
                     str(nplurals)), (_('Plural Equation'), pluralequation)]
        return [{'title': title, 'value': value} for (title, value) in
                infoparts]

    def getprojects(self, request):
        """gets the info on the projects"""

        (language_index, project_index) = \
            TranslationProject.get_language_and_project_indices()
        # self.projectcount = len(project_index) translation_projects
        # = [projects.get_translation_project(self.language, project)
        # for project in projects_] projectitems =
        # [self.getprojectitem(translation_project) for
        # translation_project in translation_projects if "view" in
        # translation_project.getrights(request.user)]
        projectitems = [self.getprojectitem(translation_project)
                        for translation_project in
                        language_index[self.language.code]]
        for (n, item) in enumerate(projectitems):
            item['parity'] = ['even', 'odd'][n % 2]
        return projectitems

    def getprojectitem(self, translation_project):
        project = translation_project.project
        href = '%s/' % project.code
        projectdescription = shortdescription(project.description)
        projectstats = translation_project.get_quick_stats()
        projectdata = self.getstats(translation_project,
                                    translation_project.directory, None)
        self.updatepagestats(projectdata['translatedsourcewords'],
                             projectdata['totalsourcewords'])
        return {
            'code': project.code,
            'href': href,
            'icon': 'folder',
            'title': project.fullname,
            'description': projectdescription,
            'data': projectdata,
            'isproject': True,
            }


class ProjectLanguageIndex(pagelayout.PootleNavPage):
    """The main page for a project, listing all the languages
    belonging to it"""

    def __init__(self, project, request):
        self.project = project
        self.projectcode = project.code
        self.initpagestats()
        languages = self.getlanguages(request)
        if len(languages) == 0:
            raise projects.Rights404Error
        average = self.getpagestats()
        projectstats = nlocalize('%d language, average %d%% translated',
                                 '%d languages, average %d%% translated',
                                 len(languages), len(languages), average)
        projectname = self.project.fullname
        description = self.project.description
        meta_description = shortdescription(description)
        instancetitle = pan_app.get_title()
        # l10n: The first parameter is the name of the installation
        # l10n: The second parameter is the name of the
        # project/language l10n: This is used as a page title. Most
        # languages won't need to change this
        pagetitle = _('%s: %s' % (instancetitle, projectname))
        templatename = 'project/project.html'
        adminlink = _('Admin')
        statsheadings = self.getstatsheadings()
        statsheadings['name'] = _('Language')

        def narrow(query):
            return limit(query.filter(translation_project__project=self.project))

        topsugg = narrow(Suggestion.objects.get_top_suggesters())
        topreview = narrow(Suggestion.objects.get_top_reviewers())
        topsub = narrow(Submission.objects.get_top_submitters())
        topstats = gentopstats(topsugg, topreview, topsub)
        templatevars = {
            'pagetitle': pagetitle,
            'project': {'code': project.code, 'name': project.fullname,
                        'stats': projectstats},
            'description': description,
            'meta_description': meta_description,
            'adminlink': adminlink,
            'languages': languages,
            'untranslatedtext': _('%s untranslated words'),
            'fuzzytext': _('%s fuzzy words'),
            'complete': _('Complete'),
            'instancetitle': instancetitle,
            'topstats': topstats,
            'topstatsheading': _('Top Contributors'),
            'statsheadings': statsheadings,
            'translationlegend': self.gettranslationsummarylegendl10n(),
            }
        pagelayout.PootleNavPage.__init__(self, templatename, templatevars,
                request, bannerheight=80)

    def getlanguages(self, request):
        """gets the stats etc of the languages"""

        (_language_index, project_index) = \
            TranslationProject.get_language_and_project_indices()
        languageitems = [self.getlanguageitem(translation_project)
                         for translation_project in
                         project_index[self.project.code]]
        for (n, item) in enumerate(languageitems):
            item['parity'] = ['even', 'odd'][n % 2]
        return languageitems

    def getlanguageitem(self, translation_project):
        language = translation_project.language
        href = '../../%s/%s/' % (language.code, self.projectcode)
        quickstats = translation_project.get_quick_stats()
        data = self.getstats(translation_project,
                             translation_project.directory, None)
        self.updatepagestats(data['translatedsourcewords'],
                             data['totalsourcewords'])
        return {
            'code': language.code,
            'icon': 'language',
            'href': href,
            'title': tr_lang(language.fullname),
            'data': data,
            }


def get_bool(dict_obj, name):
    if name in dict_obj:
        try:
            result = dict_obj[name]
            if result == '1':
                return True
            else:
                return False
        except KeyError:
            return False


def get_goal(args):
    try:
        return Goal.objects.get(name=args.pop('goal'))
    except:
        return None


