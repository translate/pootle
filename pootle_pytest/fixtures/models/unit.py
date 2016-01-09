
from collections import OrderedDict

import pytest


_UNIT_PATH_RESOLVER_TESTS = (
    ('pootle-projects-browse', {}),
    ('pootle-projects-translate', {}),
    ('pootle-project-browse',
     {"kwa": {"project_code": "project0",
              "dir_path": "",
              "filename": ""},
      "result": {"project": "project0"}}),
    ('pootle-project-translate',
     {"kwa": {"project_code": "project0",
              "dir_path": "",
              "filename": ""},
      "result": {"project": "project0"}}),

    ('pootle-project-translate_subdir',
     {"kwa": {"project_code": "project0",
              "dir_path": "subdir0/",
              "filename": ""},
      "result": {"project": "project0",
                 "directory": "subdir0/"}}),
    ('pootle-project-translate_sub_subdir',
     {"kwa": {"project_code": "project0",
              "dir_path": "subdir0/subdir1/",
              "filename": ""},
      "result": {"project": "project0",
                 "directory": "subdir0/subdir1/"}}),

    ('pootle-project-translate_subdir_filename',
     {"kwa": {"project_code": "project0",
              "dir_path": "subdir0/",
              "filename": "store0.po"},
      "result": {"project": "project0",
                 "directory": "subdir0/",
                 "filename": "store0.po"}}),
    ('pootle-project-translate_sub_subdir_filename',
     {"kwa": {"project_code": "project0",
              "dir_path": "subdir0/subdir1/",
              "filename": "store0.po"},
      "result": {"project": "project0",
                 "directory": "subdir0/subdir1/",
                 "filename": "store0.po"}}),


    ('pootle-tp-admin-permissions',
     {"kwa": {"project_code": "project0",
              "language_code": "langage0"},
      "result": {"project": "project0",
                 "language": "langage0"}}),
    ('pootle-tp-translate',
     {"kwa": {"project_code": "project0",
              "language_code": "langage0",
              "dir_path": "",
              "filename": ""},
      "result": {"project": "project0",
                 "language": "langage0"}}),
    ('pootle-tp-browse',
     {"kwa": {"project_code": "project0",
              "language_code": "langage0",
              "dir_path": "",
              "filename": ""},
      "result": {"project": "project0",
                 "language": "langage0"}}),
    ('pootle-language-browse',
     {"kwa": {"language_code": "langage0"},
      "result": {"language": "langage0"}}),
    ('pootle-language-translate',
     {"kwa": {"language_code": "langage0"},
      "result": {"language": "langage0"}}))
UNIT_PATH_RESOLVER_TESTS = OrderedDict(_UNIT_PATH_RESOLVER_TESTS)


@pytest.fixture
def unit_path_resolver_tests(unit_path_resolver_names,
                             site_matrix_with_subdirs):
    from pootle.core.url_helpers import PathResolver

    from django.core.urlresolvers import reverse

    test = UNIT_PATH_RESOLVER_TESTS[unit_path_resolver_names]
    resolved = PathResolver(
        reverse(
            unit_path_resolver_names.split("_")[0],
            kwargs=test.get("kwa", None)))
    return resolved, test
