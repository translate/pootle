#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2004-2009 Zuza Software Foundation
#
# This file is part of translate.
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

import re
import locale

from django.utils.translation import ugettext as _

from pootle_app.views import pagelayout
from pootle_app.models import Suggestion, Submission, Language, Project, \
    Directory, Goal, TranslationProject
from pootle_app.models.profile import get_profile
from pootle_app.models.permissions import get_matching_permissions
from pootle_app.models import metadata
from pootle.i18n.jtoolkit_i18n import nlocalize, tr_lang

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
        description = pagelayout.get_description()
        meta_description = shortdescription(description)
        keywords = [
            'Pootle',
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
        instancetitle = pagelayout.get_title()
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
        instancetitle = pagelayout.get_title()
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
        self.templatename = 'project/projects.html'


class LanguagesIndex(PootleIndex):
    """the list of languages"""

    def __init__(self, request):
        PootleIndex.__init__(self, request)
        self.templatename = 'language/languages.html'


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


