# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import urllib

from django import template
from django.conf import settings
from django.core.urlresolvers import reverse
from django.utils.safestring import mark_safe

from pootle.i18n.gettext import ugettext_lazy as _


register = template.Library()


@register.filter
def gravatar(user, size):
    return user.gravatar_url(size)


@register.inclusion_tag("user/includes/profile_score.html")
def profile_score(request, profile):
    context = dict(profile=profile)
    top_lang = profile.scores.top_language
    context["own_profile"] = request.user == profile.user
    if top_lang and not top_lang[0] == -1 and top_lang[1]:
        if context["own_profile"]:
            score_tweet_content = _(
                "My current score at %s is %s"
                % (settings.POOTLE_TITLE,
                   profile.scores.public_score))
            context["score_tweet_message"] = _("Tweet this!")
            context["score_tweet_link"] = (
                "https://twitter.com/share?text=%s"
                % urllib.quote_plus(score_tweet_content.encode("utf8")))
    return context


@register.inclusion_tag("user/includes/profile_ranking.html")
def profile_ranking(request, profile):
    context = dict(request=request, profile=profile)
    top_lang = profile.scores.top_language
    context["own_profile"] = request.user == profile.user
    if top_lang and not top_lang[0] == -1 and top_lang[1]:
        context["ranking_text"] = _(
            "#%s contributor in %s in the last 30 days"
            % (top_lang[0], top_lang[1].name))
        if context["own_profile"]:
            ranking_tweet_content = _(
                "I am #%s contributor in %s in the last 30 days at %s!"
                % (top_lang[0],
                   top_lang[1].name,
                   settings.POOTLE_TITLE))
            context["ranking_tweet_link"] = (
                "https://twitter.com/share?text=%s"
                % urllib.quote_plus(ranking_tweet_content.encode("utf8")))
            context["ranking_tweet_link_text"] = _("Tweet this!")
    else:
        context["no_ranking_text"] = _("No contributions in the last 30 days")
    return context


@register.inclusion_tag("user/includes/profile_social.html")
def profile_social(profile):
    links = []
    if profile.user.website:
        links.append(
            dict(url=profile.user.website,
                 icon="icon-user-website",
                 text=_("My Website")))
    if profile.user.twitter:
        links.append(
            dict(url=profile.user.twitter_url,
                 icon="icon-user-twitter",
                 text="@%s" % profile.user.twitter))
    if profile.user.linkedin:
        links.append(
            dict(url=profile.user.linkedin,
                 icon="icon-user-linkedin",
                 text=_("My LinkedIn Profile")))
    return dict(social_media_links=links)


@register.inclusion_tag("user/includes/profile_teams.html")
def profile_teams(request, profile):
    teams = profile.membership.teams_and_roles
    site_permissions = []
    if not request.user.is_anonymous and profile.user.is_superuser:
        site_permissions.append(_("Site administrator"))
    for code, info in teams.items():
        info["url"] = reverse(
            "pootle-language-browse",
            kwargs=dict(language_code=code))
    teams_title = _(
        "%s's language teams"
        % profile.user.display_name)
    no_teams_message = _(
        "%s is not a member of any language teams"
        % profile.user.display_name)
    return dict(
        anon_request=request.user.is_anonymous,
        teams=teams,
        teams_title=teams_title,
        no_teams_message=no_teams_message,
        site_permissions=site_permissions)


@register.inclusion_tag("user/includes/profile_user.html")
def profile_user(request, profile):
    context = dict(request=request, profile=profile)
    context['request_user_is_manager'] = (
        request.user.has_manager_permissions())
    if profile.user.is_anonymous:
        context["bio"] = _(
            "Some translations are provided by anonymous volunteers. "
            "These are registered under this special meta-account.")
    elif profile.user.is_system():
        context["bio"] = _(
            "Some translations are imported from external files. "
            "These are registered under this special meta-account.")
    else:
        if request.user == profile.user:
            context["can_edit_profile"] = True
            context["should_edit_profile"] = (
                not profile.user.has_contact_details
                or not profile.user.bio)
            if context["should_edit_profile"]:
                context["edit_profile_message"] = mark_safe(
                    _("Show others who you are, tell about yourself<br/>"
                      "and make your public profile look gorgeous!"))
            context["user_title"] = _(
                "You can set or change your avatar image at www.gravatar.com")
        if profile.user.bio:
            context["bio"] = profile.user.bio
    return context


@register.inclusion_tag("user/includes/profile_activity.html")
def profile_activity(profile, request_lang=None):
    context = dict(profile=profile)
    if profile.user.is_meta:
        return context
    context["user_last_event"] = (
        context["profile"].user.last_event(locale=request_lang))
    return context
