# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from pootle.core.contextmanagers import keep_data
from pootle.core.signals import update_revisions
from pootle_app.models import Directory
from pootle_app.project_tree import direct_language_match_filename
from pytest_pootle.factories import LanguageDBFactory
from pootle_store.models import Store


@pytest.mark.parametrize('language_code, path_name, matched', [
    # language codes as filenames
    (u'pt_BR', u'/path/to/pt_BR.po', True),
    (u'pt_BR', u'/path/to/pt_br.po', True),
    (u'pt-BR', u'/path/to/pt-BR.po', True),
    (u'pt-BR', u'/path/to/pt-br.po', True),
    (u'pt-br', u'/path/to/pt-BR.po', True),
    (u'pt-br', u'/path/to/pt-br.po', True),
    (u'pt_br', u'/path/to/pt_BR.po', True),
    (u'pt_br', u'/path/to/pt_br.po', True),

    # xx_YY != xx-YY
    pytest.mark.xfail((u'pt_BR', u'/path/to/pt-BR.po', True)),
    pytest.mark.xfail((u'pt_BR', u'/path/to/pt-br.po', True)),
    pytest.mark.xfail((u'pt-BR', u'/path/to/pt_BR.po', True)),
    pytest.mark.xfail((u'pt-BR', u'/path/to/pt_br.po', True)),

    (u'br', u'/path/to/br.po', True),
    (u'br', u'/path/to/BR.po', True),

    (u'kmr-Latn', u'/path/to/kmr-Latn.po', True),
    (u'ca-valencia', u'/path/to/ca-valencia.po', True),
    (u'ca@valencia', u'/path/to/ca@valencia.po', True),


    #
    # prefix == file
    #

    (u'pt_BR', u'/path/to/file-pt_BR.po', True),
    (u'pt_BR', u'/path/to/file_pt_BR.po', True),
    (u'pt_BR', u'/path/to/file.pt_BR.po', True),
    (u'pt_BR', u'/path/to/file-pt_br.po', True),
    (u'pt_BR', u'/path/to/file_pt_br.po', True),
    (u'pt_BR', u'/path/to/file.pt_br.po', True),

    # xx_YY != xx-YY
    pytest.mark.xfail((u'pt_BR', u'/path/to/file-pt-BR.po', True)),
    pytest.mark.xfail((u'pt_BR', u'/path/to/file_pt-BR.po', True)),
    pytest.mark.xfail((u'pt_BR', u'/path/to/file.pt-BR.po', True)),
    pytest.mark.xfail((u'pt_BR', u'/path/to/file-pt-br.po', True)),
    pytest.mark.xfail((u'pt_BR', u'/path/to/file_pt-br.po', True)),
    pytest.mark.xfail((u'pt_BR', u'/path/to/file.pt-br.po', True)),

    # any separator works for the most common case
    (u'br', u'/path/to/file-br.po', True),
    (u'br', u'/path/to/file_br.po', True),
    (u'br', u'/path/to/file.br.po', True),
    (u'br', u'/path/to/file-BR.po', True),
    (u'br', u'/path/to/file_BR.po', True),
    (u'br', u'/path/to/file.BR.po', True),

    # no multiple matching
    (u'br', u'/path/to/file-pt_BR.po', False),
    (u'br', u'/path/to/file_pt_BR.po', False),
    (u'br', u'/path/to/file.pt_BR.po', False),
    (u'br', u'/path/to/file-pt-BR.po', False),
    (u'br', u'/path/to/file_pt-BR.po', False),
    (u'br', u'/path/to/file.pt-BR.po', False),

    (u'br', u'/path/to/file-pt_br.po', False),
    (u'br', u'/path/to/file_pt_br.po', False),
    (u'br', u'/path/to/file.pt_br.po', False),
    (u'br', u'/path/to/file-pt-br.po', False),
    (u'br', u'/path/to/file_pt-br.po', False),
    (u'br', u'/path/to/file.pt-br.po', False),

    pytest.mark.xfail((u'kmr-Latn', u'/path/to/file-kmr-Latn.po', True)),
    pytest.mark.xfail((u'ca-valencia', u'/path/to/file-ca-valencia.po', True)),
    (u'ca@valencia', u'/path/to/file-ca@valencia.po', True),
    pytest.mark.xfail((u'ca-valencia', u'/path/help-ui-ca-valencia.po', True)),
    pytest.mark.xfail((u'ca@valencia', u'/path/help-ui-ca@valencia.po', True)),

    pytest.mark.xfail((u'kmr-Latn', u'/path/to/file.kmr-Latn.po', True)),
    pytest.mark.xfail((u'ca-valencia', u'/path/to/file.ca-valencia.po', True)),
    (u'ca@valencia', u'/path/to/file.ca@valencia.po', True),
    pytest.mark.xfail((u'ca-valencia', u'/path/help-ui.ca-valencia.po', True)),
    (u'ca@valencia', u'/path/help-ui.ca@valencia.po', True),

    #
    # template name is "pt.pot" (prefix == "pt")
    #

    # multiple matching possible
    pytest.mark.xfail((u'br', u'/path/to/pt_br.po', True)),
    pytest.mark.xfail((u'br', u'/path/to/pt_BR.po', True)),
    pytest.mark.xfail((u'br', u'/path/to/pt-br.po', True)),
    pytest.mark.xfail((u'br', u'/path/to/pt-BR.po', True)),

    # "." works as separator
    (u'br', u'/path/to/pt.br.po', True),
    (u'br', u'/path/to/pt.BR.po', True),
    (u'pt_BR', u'/path/to/pt.br.po', False),
    (u'pt_BR', u'/path/to/pt.BR.po', False),


    #
    # template name ends with "-ui" or "_ui" or ".ui"
    #

    pytest.mark.xfail((u'br', u'/path/to/help-ui-br.po', True)),
    pytest.mark.xfail((u'br', u'/path/to/help-ui_br.po', True)),
    (u'br', u'/path/to/help-ui.br.po', True),

    pytest.mark.xfail((u'br', u'/path/to/help_ui-br.po', True)),
    pytest.mark.xfail((u'br', u'/path/to/help_ui_br.po', True)),
    (u'br', u'/path/to/help_ui.br.po', True),

    pytest.mark.xfail((u'br', u'/path/to/help.ui-br.po', True)),
    pytest.mark.xfail((u'br', u'/path/to/help.ui_br.po', True)),
    (u'br', u'/path/to/help.ui.br.po', True),

    (u'br', u'/path/to/help-uiui-br.po', True),
    (u'br', u'/path/to/help_uiui-br.po', True),
    (u'br', u'/path/to/help.uiui-br.po', True),
    (u'br', u'/path/to/help-uiui_br.po', True),
    (u'br', u'/path/to/help_uiui_br.po', True),
    (u'br', u'/path/to/help.uiui_br.po', True),
    (u'br', u'/path/to/help-uiui.br.po', True),
    (u'br', u'/path/to/help_uiui.br.po', True),
    (u'br', u'/path/to/help.uiui.br.po', True),

    #
    # "-" separator
    #

    (u'pt_BR', u'/path/to/help-ui-pt_BR.po', True),
    (u'pt_BR', u'/path/to/help_ui-pt_BR.po', True),
    (u'pt_BR', u'/path/to/help.ui-pt_BR.po', True),

    # xx_YY != xx-YY
    pytest.mark.xfail((u'pt_BR', u'/path/to/help-ui-pt-BR.po', True)),
    pytest.mark.xfail((u'pt_BR', u'/path/to/help_ui-pt-BR.po', True)),
    pytest.mark.xfail((u'pt_BR', u'/path/to/help.ui-pt-BR.po', True)),

    (u'pt_BR', u'/path/to/help-ui-pt_br.po', True),
    (u'pt_BR', u'/path/to/help_ui-pt_br.po', True),
    (u'pt_BR', u'/path/to/help.ui-pt_br.po', True),

    # xx_YY != xx-YY
    pytest.mark.xfail((u'pt_BR', u'/path/to/help-ui-pt-br.po', True)),
    pytest.mark.xfail((u'pt_BR', u'/path/to/help_ui-pt-br.po', True)),
    pytest.mark.xfail((u'pt_BR', u'/path/to/help.ui-pt-br.po', True)),

    #
    #  "_" separator
    #

    (u'pt_BR', u'/path/to/help-ui_pt_BR.po', True),
    (u'pt_BR', u'/path/to/help_ui_pt_BR.po', True),
    (u'pt_BR', u'/path/to/help.ui_pt_BR.po', True),

    # xx_YY != xx-YY
    pytest.mark.xfail((u'pt_BR', u'/path/to/help-ui_pt-BR.po', True)),
    pytest.mark.xfail((u'pt_BR', u'/path/to/help_ui_pt-BR.po', True)),
    pytest.mark.xfail((u'pt_BR', u'/path/to/help.ui_pt-BR.po', True)),

    (u'pt_BR', u'/path/to/help-ui_pt_br.po', True),
    (u'pt_BR', u'/path/to/help_ui_pt_br.po', True),
    (u'pt_BR', u'/path/to/help.ui_pt_br.po', True),

    pytest.mark.xfail((u'pt_BR', u'/path/to/help-ui_pt-br.po', True)),
    pytest.mark.xfail((u'pt_BR', u'/path/to/help_ui_pt-br.po', True)),
    pytest.mark.xfail((u'pt_BR', u'/path/to/help.ui_pt-br.po', True)),

    #
    #  "." separator
    #
    (u'pt_BR', u'/path/to/help-ui.pt_BR.po', True),
    (u'pt_BR', u'/path/to/help_ui.pt_BR.po', True),
    (u'pt_BR', u'/path/to/help.ui.pt_BR.po', True),

    # xx_YY != xx-YY
    pytest.mark.xfail((u'pt_BR', u'/path/to/help-ui.pt-BR.po', True)),
    pytest.mark.xfail((u'pt_BR', u'/path/to/help_ui.pt-BR.po', True)),
    pytest.mark.xfail((u'pt_BR', u'/path/to/help.ui.pt-BR.po', True)),

    (u'pt_BR', u'/path/to/help-ui.pt_br.po', True),
    (u'pt_BR', u'/path/to/help_ui.pt_br.po', True),
    (u'pt_BR', u'/path/to/help.ui.pt_br.po', True),

    # xx_YY != xx-YY
    pytest.mark.xfail((u'pt_BR', u'/path/to/help-ui.pt-br.po', True)),
    pytest.mark.xfail((u'pt_BR', u'/path/to/help_ui.pt-br.po', True)),
    pytest.mark.xfail((u'pt_BR', u'/path/to/help.ui.pt-br.po', True)),



])
@pytest.mark.django_db
def test_direct_language_match_filename(language_code, path_name, matched):

    with keep_data(signals=(update_revisions, ), suppress=(Directory, Store)):
        LanguageDBFactory(code="pt_BR")

    assert direct_language_match_filename(language_code, path_name) is matched
