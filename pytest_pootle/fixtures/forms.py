from collections import OrderedDict
from copy import deepcopy
from datetime import datetime, timedelta
import urllib

import pytest

from ..utils import create_api_request


UNITS_FORM_DEFAULT_DATA = {
    'count': 9, 'category': u'',
    'sort_on': 'units',
    'uids': [], 'initial': False,
    'month': None, 'filter': u'',
    'sort_by': None, 'vfolder': None,
    'modified_since': None, 'sort_by_param': u'',
    "language": None, "project": None, "dir_path": "",
    "filename": "", "search": "", "sfields": [], "soptions": []}

DAY_AGO = (datetime.now() - timedelta(days=1))
MONTH_AGO = (datetime.now() - timedelta(days=30))
TWO_MONTHS_AGO = (datetime.now() - timedelta(days=60))


def get_untranslated_uid():
    from pootle_store.models import Unit
    from pootle_store.util import UNTRANSLATED

    units = Unit.objects.filter(state=UNTRANSLATED)
    index = (
        units.count() / 2)
    return units[index].id


def get_translated_uid():
    from pootle_store.models import Unit
    from pootle_store.util import TRANSLATED

    units = Unit.objects.filter(state=TRANSLATED)
    index = (
        units.count() / 2)
    return units[index].id

_UNITS_FORM = [
    ("default_path",
     {"get": {"path": ""}}),
    ("state_translated",
     {"get": {"path": "", "filter": "translated"},
      "data": {"filter": "translated"}})]

UNITS_FORM = OrderedDict()
UNITS_FORM["default_path"] = {"get": {"path": ""}}
UNITS_FORM["state_translated"] = {
    "get": {"path": "", "filter": "translated"},
    "data": {"filter": "translated"}}
UNITS_FORM["state_untranslated"] = {
    "get": {"path": "", "filter": "untranslated"},
    "data": {"filter": "untranslated"}}
UNITS_FORM["state_incomplete"] = {
    "get": {"path": "", "filter": "incomplete"},
    "data": {"filter": "incomplete"}}
UNITS_FORM["state_fuzzy"] = {
    "get": {"path": "", "filter": "fuzzy"},
    "data": {"filter": "fuzzy"}}

UNITS_FORM["sort_units_oldest"] = {
    "get": {"path": "",
            "sort_by_param": "oldest"},
    "data": {"sort_by": "submitted_on",
             "sort_by_param": "oldest"}}

UNITS_FORM["filter_translated_from_uid"] = {
    "get": {"path": "",
            "uids": get_translated_uid,
            "filter": "translated",
            "sort_by_param": "oldest"},
    "data": {"sort_by": "submitted_on",
             "sort_by_param": "oldest",
             "filter": "translated"}}


UNITS_FORM["modified_last_month"] = {
    "get": {"path": "",
            "modified_since": MONTH_AGO.isoformat()},
    "data": {"modified_since": MONTH_AGO}}
UNITS_FORM["modified_last_two_months"] = {
    "get": {"path": "",
            "modified_since": TWO_MONTHS_AGO.isoformat()},
    "data": {"modified_since": TWO_MONTHS_AGO}}
UNITS_FORM["modified_last_day"] = {
    "get": {"path": "",
            "modified_since": DAY_AGO.isoformat()},
    "data": {"modified_since": DAY_AGO}}


UNITS_FORM["filter_suggestions"] = {
    "get": {"path": "",
            "filter": "suggestions"},
    "data": {'filter': 'suggestions',
             'sort_on': 'suggestions'}}
UNITS_FORM["filter_user_suggestions"] = {
    "get": {"path": "",
            "filter": "user-suggestions"},
    "data": {'filter': 'user-suggestions',
             'sort_on': 'suggestions'}}
UNITS_FORM["filter_user_suggestions_accepted"] = {
    "get": {"path": "",
            "filter": "user-suggestions-accepted"},
    "data": {'filter': 'user-suggestions-accepted'}}
UNITS_FORM["filter_user_suggestions_rejected"] = {
    "get": {"path": "",
            "filter": "user-suggestions-rejected"},
    "data": {'filter': 'user-suggestions-rejected'}}


UNITS_FORM["filter_user_submissions"] = {
    "get": {"path": "",
            "filter": "user-submissions"},
    "data": {'filter': 'user-submissions',
             'sort_on': 'submissions'}}
UNITS_FORM["filter_user_submissions_overwritten"] = {
    "get": {"path": "",
            "filter": "user-submissions-overwritten"},
    "data": {'filter': 'user-submissions-overwritten'}}


UNITS_FORM["filter_search_empty"] = {
    "get": {"path": "",
            "search": "FOO", "sfields": "source"},
    "data": {"sfields": [u"source"], "search": "FOO"}}
UNITS_FORM["filter_search_untranslated"] = {
    "get": {"path": "",
            "search": "untranslated", "sfields": "source"},
    "data": {"sfields": [u"source"], "search": "untranslated"}}


UNITS_FORM["sort_my_suggestion_oldest"] = {
    "get": {"path": "",
            "sort_by_param": "oldest",
            "filter": "user-suggestions"},
    "data": {
        "sort_by": "suggestion__creation_time",
        'filter': 'user-suggestions',
        'sort_on': 'suggestions',
        'sort_by_param': 'oldest'}}


@pytest.fixture
def units_form_tests(rf, default, member, member2,
                     units_form_test_names):

    from django.contrib.auth import get_user_model

    from pootle_store.forms import UnitSearchForm

    User = get_user_model()

    params = deepcopy(UNITS_FORM[units_form_test_names])

    url = "/"
    if "get" in params:
        for k, v in params["get"].items():
            if callable(v):
                params["get"][k] = v()
        url = "/?%s" % urllib.urlencode(params["get"])

    request_user = params.get("request_user", "default")
    user = User.objects.get(username=request_user)
    request = create_api_request(rf, url=url, user=user)
    form = UnitSearchForm(request.GET, user=user)

    if not params.get("valid", None) is False:
        params["cleaned_data"] = UNITS_FORM_DEFAULT_DATA.copy()
        params["cleaned_data"].update(params.get("data", {}))

    return (form, params, default, member, member2)


@pytest.fixture
def units_search_tests(rf, units_form_test_names):
    from django.contrib.auth import get_user_model

    from pootle_store.unit.search import UnitSearch
    from pootle_store.models import Unit

    User = get_user_model()

    params = deepcopy(UNITS_FORM[units_form_test_names])

    request_user = params.get("request_user", "default")
    user = User.objects.get(username=request_user)
    params["cleaned_data"] = UNITS_FORM_DEFAULT_DATA.copy()
    params["cleaned_data"].update(params.get("data", {}))

    if "get" in params:
        if "uids" in params["get"]:
            params["cleaned_data"]["uids"] = [params["get"]["uids"]()]
    params["cleaned_data"]['path'] = unicode(params["get"]["path"])
    params["cleaned_data"]['pootle_path'] = params["cleaned_data"]['path']

    limit = params.get("limit", None)
 
    qs = Unit.objects.get_for_path(
        params["cleaned_data"]["pootle_path"],
        user)
    search = UnitSearch(
        qs=qs,
        limit=limit,
        user=user, **params["cleaned_data"])

    return (search, params, user, limit, qs)


@pytest.fixture
def units_filter_tests(rf, units_form_test_names):
    from django.contrib.auth import get_user_model

    from pootle_store.unit.filters import SearchFilter
    from pootle_store.models import Unit

    User = get_user_model()
    params = deepcopy(UNITS_FORM[units_form_test_names])
    request_user = params.get("request_user", "default")
    user = User.objects.get(username=request_user)
    params["cleaned_data"] = UNITS_FORM_DEFAULT_DATA.copy()
    params["cleaned_data"].update(params.get("data", {}))

    # TODO: allow this to be overridden in get
    params["cleaned_data"]["user"] = user
    params["cleaned_data"]['path'] = unicode(params["get"]["path"])
    params["cleaned_data"]['pootle_path'] = params["cleaned_data"]['path']

    if "get" in params:
        if "uids" in params["get"]:
            params["cleaned_data"]["uids"] = [params["get"]["uids"]()]
 
    qs = Unit.objects.get_translatable(
        user,
        project_code=params["cleaned_data"]["project"],
        language_code=params["cleaned_data"]["language"])
    unit_filter = SearchFilter(qs=qs)
    return (unit_filter, params, user, qs)
