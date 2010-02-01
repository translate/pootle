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

import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'pootle.settings'

from django.db import transaction

from django.core.management.base import NoArgsCommand
from django.contrib.auth.models import User

class Command(NoArgsCommand):
    def handle_noargs(self, **options):
        create_default_db()

def create_default_db():
    """This creates the default database to get a working Pootle installation.

    You can tweak the methods called or their implementation elsewhere in the
    file. This provides some sane default to get things working."""
    try:
        try:
            transaction.enter_transaction_management()
            transaction.managed(True)

            create_default_projects()
            create_default_languages()
            create_default_admin()
        except:
            if transaction.is_dirty():
                transaction.rollback()
            transaction.leave_transaction_management()
            raise
    finally:
        if transaction.is_managed():
            if transaction.is_dirty():
                transaction.commit()
            transaction.leave_transaction_management()

def create_default_projects():
    """Create the default projects that we host. You might want to add your
    projects here, although you can also add things through the web interface
    later."""
    from pootle_project.models import Project

    pootle = Project(code=u"pootle")
    pootle.fullname = u"Pootle"
    pootle.description = "<div dir='ltr' lang='en'>Interface translations for Pootle. <br /> See the <a href='http://pootle.locamotion.org'>official Pootle server</a> for the translations of Pootle.</div>"
    pootle.checkstyle = "standard"
    pootle.localfiletype = "po"
    pootle.treestyle = "auto"
    pootle.save()

    tutorial = Project(code=u"tutorial")
    tutorial.fullname = u"Tutorial"
    tutorial.description = "<div dir='ltr' lang='en'>Tutorial project where users can play with Pootle and learn more about translation and localisation.<br />For more help on localisation, visit the <a href='http://translate.sourceforge.net/wiki/guide/start'>localisation guide</a>.</div>"
    tutorial.checkstyle = "standard"
    tutorial.localfiletype = "po"
    tutorial.treestyle = "auto"
    tutorial.save()

def create_default_languages():
    """Create the default languages. We afford this priviledge to languages
    with reasonably complete interface translations for Pootle."""
    from pootle_language.models import Language

    af = Language(code="af")
    af.fullname = u"Afrikaans"
    af.specialchars = u"ëïêôûáéíóúý"
    af.nplurals = '2'
    af.pluralequation = "(n != 1)"
    af.save()

    # Akan
    ak = Language(code='ak')
    ak.fullname = u'Akan'
    ak.pluralequation = u'(n > 1)'
    ak.specialchars = "ɛɔƐƆ"
    ak.nplurals = u'2'
    ak.save()

    # Haitian Creole
    ht = Language(code="ht")
    ht.fullname = u'Haitian; Haitian Creole'
    ht.nplurals = '2'
    ht.pluralequation = '(n != 1)'
    ht.save()

    # Sesotho sa Leboa
    # Northern Sotho
    nso = Language(code="nso")
    nso.fullname = u'Pedi; Sepedi; Northern Sotho": u"Northern Sotho'
    nso.nplurals = '2'
    nso.pluralequation = '(n > 1)'
    nso.specialchars = "šŠ"
    nso.save()

    # Tshivenḓa
    # Venda
    ve = Language(code="ve")
    ve.fullname = u'Venda'
    ve.nplurals = '2'
    ve.pluralequation = '(n != 1)'
    ve.specialchars = "ḓṋḽṱ ḒṊḼṰ ṅṄ"
    ve.save()

    # Wolof
    wo = Language(code="wo")
    wo.fullname = u'Wolof'
    wo.nplurals = '2'
    wo.pluralequation = '(n != 1)'
    wo.save()

    # 简体中文
    # Simplified Chinese (China mainland used below, but also used in Singapore and Malaysia)
    zh_CN = Language(code="zh_CN")
    zh_CN.fullname = u'Chinese (China)'
    zh_CN.nplurals = '1'
    zh_CN.pluralequation = '0'
    zh_CN.specialchars = u"←→↔×÷©…—‘’“”【】《》"
    zh_CN.save()

    # 繁體中文
    # Traditional Chinese (Hong Kong used below, but also used in Taiwan and Macau)
    zh_HK = Language(code="zh_HK")
    zh_HK.fullname = u'Chinese (Hong Kong)'
    zh_HK.nplurals = '1'
    zh_HK.pluralequation = '0'
    zh_HK.specialchars = u"←→↔×÷©…—‘’“”「」『』【】《》"
    zh_HK.save()

    # 繁體中文
    # Traditional Chinese (Taiwan used below, but also used in Hong Kong and Macau)
    zh_TW = Language(code="zh_TW")
    zh_TW.fullname = u'Chinese (Taiwan)'
    zh_TW.nplurals = '1'
    zh_TW.pluralequation = '0'
    zh_TW.specialchars = u"←→↔×÷©…—‘’“”「」『』【】《》"
    zh_TW.save()

    ca_valencia = Language(code='ca@valencia')
    ca_valencia.fullname = u'Catalan (Valencia)'
    ca_valencia.nplurals = '2'
    ca_valencia.pluralequation = '(n != 1)'
    ca_valencia.save()

    son = Language(code='son')
    son.fullname = u'Songhai languages'
    son.nplurals = '1'
    son.pluralequation = '0'
    son.specialchars = u'ɲŋšžãõẽĩƝŊŠŽÃÕẼĨ'
    son.save()

    # import languages from toolkit
    from translate.lang import data
    for code, props in data.languages.items():
        try:
            lang, created = Language.objects.get_or_create(code=code, fullname=props[0],
                                             nplurals=props[1], pluralequation=props[2])
        except:
            pass


def create_default_admin():
    """Create the default user(s) for Pootle. You definitely want to change
    the admin account so that your default install is not accessible with the
    default credentials. The users 'noboby' and 'default' should be left as is."""
    admin = User(username=u"admin",
                first_name=u"Administrator",
                is_active=True,
                is_superuser=True,
                is_staff=True)
    admin.set_password("admin")
    admin.save()
