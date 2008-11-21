#!/usr/bin/env python
# coding: utf-8
from sqlalchemy import *
from sqlalchemy.orm import *
from sqlalchemy.ext.declarative import declarative_base
from dbclasses import *
import sys
from jToolkit import prefs
import md5

def main():
  if len(sys.argv) != 2:
    print "Usage: %s pootle.prefs" % sys.argv[0]
    return

  prefsfile = sys.argv[1]
  pref = prefs.PrefsParser(prefsfile)
  session = configDB(pref.Pootle)
  create_default_db(session)

def configDB(instance):
  # Set up the connection options
  STATS_OPTIONS = {}
  for k,v in instance.stats.connect.iteritems():
    STATS_OPTIONS[k] = v

  #metadata = Base.metadata
  engine = create_engine('sqlite:///%s' % STATS_OPTIONS['database'])
  conn = engine.connect()

  Session = sessionmaker(bind=engine, autoflush=True)
  alchemysession = Session()

  metadata.create_all(engine)

  return alchemysession

def create_default_db(s):
  create_default_projects(s)
  create_default_languages(s)
  create_default_users(s)

def attempt(s,obj):
  print "Adding %s... " % (str(obj)),
  try:
    s.add(obj)
    s.commit()
  except Exception, e:
    s.rollback()
    print "FAILED: %s" % e
  else:
    print "OK"

def create_default_projects(s):
  pootle = Project(u"pootle")
  pootle.fullname = u"Pootle"
  pootle.description = "<div dir='ltr' lang='en'>Interface translations for Pootle. <br /> See the <a href='http://pootle.locamotion.org'>official Pootle server</a> for the translations of Pootle.</div>"
  pootle.checkstyle = "standard"
  pootle.localfiletype = "po"
  attempt(s,pootle)

  terminology = Project(u"terminology")
  terminology.fullname = u"Terminology"
  terminology.description = "<div dir='ltr' lang='en'>Terminology project that Pootle should use to suggest terms.<br />There might be useful terminology files on the <a href='http://pootle.locamotion.org/projects/terminology/'>official Pootle server</a>.</div>"
  terminology.checkstyle = "standard"
  terminology.localfiletype = "po"
  attempt(s,terminology)

def create_default_languages(s):
    af = Language("af")
    af.fullname = u"Afrikaans"
    af.specialchars = u"ëïêôûáéíóúý"
    af.nplurals = '2'
    af.pluralequation = "(n != 1)"
    attempt(s,af)

# Akan
#    ak.fullname = u'Akan'
#    ak.pluralequation = u'(n > 1)'
#    ak.specialchars = "ɛɔƐƆ"
#    ak.nplurals = u'2'

# العربية
# Arabic
    ar = Language("ar")
    ar.fullname = u'Arabic'
    ar.nplurals = '6'
    ar.pluralequation ='n==0 ? 0 : n==1 ? 1 : n==2 ? 2 : n%100>=3 && n%100<=10 ? 3 : n%100>=11 && n%100<=99 ? 4 : 5'
    attempt(s,ar)

# Azərbaycan
# Azerbaijani
#    az.fullname = u'Azerbaijani'
#    az.nplurals = '2'
#    az.pluralequation ='(n != 1)'

# Беларуская
# Belarusian
#    be.fullname = u'Belarusian'
#    be.nplurals = '3'
#    be.pluralequation ='(n%10==1 && n%100!=11 ? 0 : n%10>=2 && n%10<=4 && (n%100<10 || n%100>=20) ? 1 : 2)'

# Български
# Bulgarian
#    bg.fullname = u'Bulgarian'
#    bg.nplurals = '2'
#    bg.pluralequation ='(n != 1)'

# বাংলা
# Bengali
#    bn.fullname = u'Bengali'
#    bn.nplurals = '2'
#    bn.pluralequation ='(n != 1)'

# Tibetan
#    bo.fullname = u'Tibetan'
#    bo.nplurals = '1'
#    bo.pluralequation ='0'

# Bosanski
# Bosnian
#    bs.fullname = u'Bosnian'
#    bs.nplurals = '3'
#    bs.pluralequation ='(n%10==1 && n%100!=11 ? 0 : n%10>=2 && n%10<=4 && (n%100<10 || n%100>=20) ? 1 : 2)'

# Català
# Catalan
    ca = Language("ca")
    ca.fullname = u'Catalan; Valencian'
    ca.nplurals = '2'
    ca.pluralequation ='(n != 1)'
    attempt(s,ca)

# Česky
# Czech
    cs = Language("cs")
    cs.fullname = u'Czech'
    cs.nplurals = '3'
    cs.pluralequation ='(n==1) ? 0 : (n>=2 && n<=4) ? 1 : 2'
    attempt(s,cs)

# Cymraeg
# Welsh
#    cy.fullname = u'Welsh'
#    cy.nplurals = '2'
#    cy.pluralequation ='(n==2) ? 1 : 0'

# Dansk
# Danish
    da = Language("da")
    da.fullname = u'Danish'
    da.nplurals = '2'
    da.pluralequation ='(n != 1)'
    attempt(s,da)

# Deutsch
# German
    de = Language("de")
    de.fullname = u'German'
    de.nplurals = '2'
    de.pluralequation ='(n != 1)'
    attempt(s,de)

# ང་ཁ
# Dzongkha
#    dz.fullname = u'Dzongkha'
#    dz.nplurals = '1'
#    dz.pluralequation ='0'

# Ελληνικά
# Greek
    el = Language("el")
    el.fullname = u'Greek'
    el.nplurals = '2'
    el.pluralequation ='(n != 1)'
    attempt(s,el)

# English
    en = Language("en")
    en.fullname = u'English'
    en.nplurals = '2'
    en.pluralequation ='(n != 1)'
    attempt(s,en)

# English (United Kingdom)
    en_GB = Language("en_GB")
    en_GB.fullname = u'English (United Kingdom)'
    en_GB.nplurals = '2'
    en_GB.pluralequation ='(n != 1)'
    attempt(s,en_GB)

# English (US)
    en_US = Language("en_US")
    en_US.fullname = u'English'
    en_US.nplurals = '2'
    en_US.pluralequation ='(n != 1)'
    attempt(s,en_US)

# English (South Africa)
    en_ZA = Language("en_ZA")
    en_ZA.fullname = u'English (South Africa)'
    en_ZA.nplurals = '2'
    en_ZA.pluralequation ='(n != 1)'
    attempt(s,en_ZA)

# Esperanto
#    eo.fullname = u'Esperanto'
#    eo.nplurals = '2'
#    eo.pluralequation ='(n != 1)'

# Español
# Spanish
    es = Language("es")
    es.fullname = u'Spanish; Castilian'
    es.nplurals = '2'
    es.pluralequation ='(n != 1)'
    attempt(s,es)

# Español
# Spanish (Argentina)
    es_AR = Language("es_AR")
    es_AR.fullname = u'Spanish (Argentina)'
    es_AR.nplurals = '2'
    es_AR.pluralequation ='(n != 1)'
    attempt(s,es_AR)

# Español
# Spanish (Spain)
    es_ES = Language("es_ES")
    es_ES.fullname = u'Spanish (Spain)'
    es_ES.nplurals = '2'
    es_ES.pluralequation ='(n != 1)'
    attempt(s,es_ES)

# Eesti
# Estonian
#    et.fullname = u'Estonian'
#    et.nplurals = '2'
#    et.pluralequation ='(n != 1)'

# Euskara
# Basque
    eu = Language("eu")
    eu.fullname = u'Basque'
    eu.nplurals = '2'
    eu.pluralequation ='(n != 1)'
    attempt(s,eu)

# فارسی
# Persian
    fa = Language("fa")
    fa.fullname = u'Persian'
    fa.nplurals = '1'
    fa.pluralequation ='0'
    attempt(s,fa)

# Suomi
# Finnish
    fi = Language("fi")
    fi.fullname = u'Finnish'
    fi.nplurals = '2'
    fi.pluralequation ='(n != 1)'
    attempt(s,fi)

# Føroyskt
# Faroese
#    fo.fullname = u'Faroese'
#    fo.nplurals = '2'
#    fo.pluralequation ='(n != 1)'

# Français
# French
    fr = Language("fr")
    fr.fullname = u'French'
    fr.nplurals = '2'
    fr.pluralequation ='(n > 1)'
    attempt(s,fr)

# Furlan
# Friulian
    fur = Language("fur")
    fur.fullname = u'Friulian'
    fur.nplurals = '2'
    fur.pluralequation ='(n != 1)'
    attempt(s,fur)

# Frysk
# Frisian
#    fy.fullname = u'Western Frisian'
#    fy.nplurals = '2'
#    fy.pluralequation ='(n != 1)'

# Frysk
# Frisian
    fy_NL = Language("fy_NL")
    fy_NL.fullname = u'Frisian'
    fy_NL.nplurals = '2'
    fy_NL.pluralequation ='(n != 1)'
    attempt(s,fy_NL)

# Gaeilge
# Irish
#    ga.fullname = u'Irish'
#    ga.nplurals = '3'
#    ga.pluralequation ='n==1 ? 0 : n==2 ? 1 : 2'

# Gaeilge
# Irish
    ga_IE = Language("ga_IE")
    ga_IE.fullname = u'Irish'
    ga_IE.nplurals = '3'
    ga_IE.pluralequation ='n==1 ? 0 : n==2 ? 1 : 2'
    attempt(s,ga_IE)

# Galego
# Galician
    gl = Language("gl")
    gl.fullname = u'Galician'
    gl.nplurals = '2'
    gl.pluralequation ='(n != 1)'
    attempt(s,gl)

# ગુજરાતી
# Gujarati
#    gu.fullname = u'Gujarati'
#    gu.nplurals = '2'
#    gu.pluralequation ='(n != 1)'

# עברית
# Hebrew
    he = Language("he")
    he.fullname = u'Hebrew'
    he.nplurals = '2'
    he.pluralequation ='(n != 1)'
    attempt(s,he)

# हिन्दी
# Hindi
#    hi.fullname = u'Hindi'
#    hi.nplurals = '2'
#    hi.pluralequation ='(n != 1)'

# Hrvatski
# Croatian
#    hr.fullname = u'Croatian'
#    hr.nplurals = '3'
#    hr.pluralequation ='(n%10==1 && n%100!=11 ? 0 : n%10>=2 && n%10<=4 && (n%100<10 || n%100>=20) ? 1 : 2)'

# Magyar
# Hungarian
    hu = Language("hu")
    hu.fullname = u'Hungarian'
    hu.nplurals = '2'
    hu.pluralequation ='(n !=1)'
    attempt(s,hu)

# Bahasa Indonesia
# Indonesian
    id = Language("id")
    id.fullname = u'Indonesian'
    id.nplurals = '1'
    id.pluralequation ='0'
    attempt(s,id)

# Icelandic
    islang = Language("is")
    islang.fullname = u'Icelandic'
    islang.nplurals = '2'
    islang.pluralequation = '(n != 1)'
    attempt(s,islang)

# Italiano
# Italian
    it = Language("it")
    it.fullname = u'Italian'
    it.nplurals = '2'
    it.pluralequation ='(n != 1)'
    attempt(s,it)

# 日本語
# Japanese
    ja = Language("ja")
    ja.fullname = u'Japanese'
    ja.nplurals = '1'
    ja.pluralequation ='0'
    attempt(s,ja)

# ქართული
# Georgian
    ka = Language("ka")
    ka.fullname = u'Georgian'
    ka.nplurals = '1'
    ka.pluralequation ='0'
    attempt(s,ka)

# ភាសា
# Khmer
#    km.fullname = u'Khmer'
#    km.nplurals = '1'
#    km.pluralequation ='0'

# 한국어
# Korean
    ko = Language("ko")
    ko.fullname = u'Korean'
    ko.nplurals = '1'
    ko.pluralequation ='0'
    attempt(s,ko)

# Kurdî / كوردي
# Kurdish
#    ku.fullname = u'Kurdish'
#    ku.nplurals = '2'
#    ku.pluralequation ='(n!= 1)'

# Lëtzebuergesch
# Letzeburgesch
#    lb.fullname = u'Letzeburgesch'
#    lb.nplurals = '2'
#    lb.pluralequation ='(n != 1)'

# Lietuvių
# Lithuanian
    lt = Language("lt")
    lt.fullname = u'Lithuanian'
    lt.nplurals = '3'
    lt.pluralequation ='(n%10==1 && n%100!=11 ? 0 : n%10>=2 && (n%100<10 || n%100>=20) ? 1 : 2)'
    attempt(s,lt)

# Latviešu
# Latvian
#    lv.fullname = u'Latvian'
#    lv.nplurals = '3'
#    lv.pluralequation ='(n%10==1 && n%100!=11 ? 0 : n != 0 ? 1 : 2)'

# Malayalam
    ml = Language("ml")
    ml.fullname = u'Malayalam'
    ml.nplurals = '2'
    ml.pluralequation = '(n != 1)'
    attempt(s,ml)

# Malagasy
#    mg.fullname = u'Malagasy'
#    mg.nplurals = '2'
#    mg.pluralequation ='(n > 1)'

# Монгол
# Mongolian
    mn = Language("mn")
    mn.fullname = u'Mongolian'
    mn.nplurals = '2'
    mn.pluralequation ='(n != 1)'
    attempt(s,mn)

# Marathi
#    mr.fullname = u'Marathi'
#    mr.nplurals = u'2'
#    mr.pluralequation = u'(n != 1)'

# Malay
#    ms.fullname = u'Malay'
#    ms.nplurals = u'1'
#    ms.pluralequation = u'0'

# Malti
# Maltese
    mt = Language("mt")
    mt.fullname = u'Maltese'
    mt.nplurals = '4'
    mt.pluralequation ='(n==1 ? 0 : n==0 || ( n%100>1 && n%100<11) ? 1 : (n%100>10 && n%100<20 ) ? 2 : 3)'
    attempt(s,mt)

# Nahuatl
#    nah.fullname = u'Nahuatl'
#    nah.nplurals = '2'
#    nah.pluralequation ='(n != 1)'

# Bokmål
# Norwegian Bokmal
#    nb.fullname = u'Norwegian Bokmal'
#    nb.nplurals = '2'
#    nb.pluralequation ='(n != 1)'

# Nepali
#    ne.fullname = u'Nepali'
#    ne.nplurals = u'2'
#    ne.pluralequation = u'(n != 1)'

# Nederlands
# Dutch
    nl = Language("nl")
    nl.fullname = u'Dutch; Flemish'
    nl.nplurals = '2'
    nl.pluralequation ='(n != 1)'
    attempt(s,nl)

# Nynorsk
# Norwegian Nynorsk
#    nn.fullname = u'Norwegian Nynorsk'
#    nn.nplurals = '2'
#    nn.pluralequation ='(n != 1)'

# Sesotho sa Leboa
# Northern Sotho
#    nso.fullname = u'Northern Sotho'
#    nso.nplurals = '2'
#    nso.pluralequation ='(n > 1)'
#    nso.specialchars = "šŠ"

# Oriya
#    or.fullname = u'Oriya'
#    or.nplurals = '2'
#    or.pluralequation ='(n != 1)'

# Punjabi
#    pa.fullname = u'Panjabi; Punjabi'
#    pa.nplurals = '2'
#    pa.pluralequation ='(n != 1)'

# Papiamento
#    pap.fullname = u'Papiamento'
#    pap.nplurals = '2'
#    pap.pluralequation ='(n != 1)'

# Polski
# Polish
    pl = Language("pl")
    pl.fullname = u'Polish'
    pl.nplurals = '3'
    pl.pluralequation ='(n==1 ? 0 : n%10>=2 && n%10<=4 && (n%100<10 || n%100>=20) ? 1 : 2)'
    attempt(s,pl)

# Português
# Portuguese
    pt = Language("pt")
    pt.fullname = u'Portuguese'
    pt.nplurals = '2'
    pt.pluralequation ='(n != 1)'
    attempt(s,pt)

# Português
# Portuguese from Portugal
    pt_PT = Language("pt_PT")
    pt_PT.fullname = u'Portuguese (Portugal)'
    pt_PT.nplurals = '2'
    pt_PT.pluralequation ='(n != 1)'
    attempt(s,pt_PT)

# Português do Brasil
# Brazilian Portuguese
    pt_BR = Language("pt_BR")
    pt_BR.fullname = u'Portuguese (Brazil)'
    pt_BR.nplurals = '2'
    pt_BR.pluralequation ='(n > 1)'
    attempt(s,pt_BR)

# Română
# Romanian
    ro = Language("ro")
    ro.fullname = u'Romanian'
    ro.nplurals = '3'
    ro.pluralequation ='(n==1 ? 0 : (n==0 || (n%100 > 0 && n%100 < 20)) ? 1 : 2);'
    attempt(s,ro)

# Русский
# Russian
    ru = Language("ru")
    ru.fullname = u'Russian'
    ru.nplurals = '3'
    ru.pluralequation ='(n%10==1 && n%100!=11 ? 0 : n%10>=2 && n%10<=4 && (n%100<10 || n%100>=20) ? 1 : 2)'
    attempt(s,ru)

# Slovenčina
# Slovak
    sk = Language("sk")
    sk.fullname = u'Slovak'
    sk.nplurals = '3'
    sk.pluralequation ='(n==1) ? 0 : (n>=2 && n<=4) ? 1 : 2'
    attempt(s,sk)

# Slovenščina
# Slovenian
    sl = Language("sl")
    sl.fullname = u'Slovenian'
    sl.nplurals = '4'
    sl.pluralequation ='(n%100==1 ? 0 : n%100==2 ? 1 : n%100==3 || n%100==4 ? 2 : 3)'
    attempt(s,sl)

# Shqip
# Albanian
    sq = Language("sq")
    sq.fullname = u'Albanian'
    sq.nplurals = '2'
    sq.pluralequation ='(n != 1)'
    attempt(s,sq)

# Српски / Srpski
# Serbian
    sr = Language("sr")
    sr.fullname = u'Serbian'
    sr.nplurals = '3'
    sr.pluralequation ='(n%10==1 && n%100!=11 ? 0 : n%10>=2 && n%10<=4 && (n%100<10 || n%100>=20) ? 1 : 2)'
    attempt(s,sr)

# Sesotho
# Sotho
    st = Language("st")
    st.fullname = u'Sotho, Southern'
    st.nplurals = '2'
    st.pluralequation ='(n != 1)'
    attempt(s,st)

# Svenska
# Swedish
    sv = Language("sv")
    sv.fullname = u'Swedish'
    sv.nplurals = '2'
    sv.pluralequation ='(n != 1)'
    attempt(s,sv)

# Svenska
# Swedish (Sweden)
    sv_SE = Language("sv_SE")
    sv_SE.fullname = u'Swedish (Sweden)'
    sv_SE.nplurals = '2'
    sv_SE.pluralequation ='(n != 1)'
    attempt(s,sv_SE)

# தமிழ்
# Tamil
#    ta.fullname = u'Tamil'
#    ta.nplurals = '2'
#    ta.pluralequation ='(n != 1)'

# Туркмен / تركمن
# Turkmen
#    tk.fullname = u'Turkmen'
#    tk.nplurals = '2'
#    tk.pluralequation ='(n != 1)'

# Türkçe
# Turkish
    tr = Language("tr")
    tr.fullname = u'Turkish'
    tr.nplurals = '1'
    tr.pluralequation ='0'
    attempt(s,tr)

# Українська
# Ukrainian
    uk = Language("uk")
    uk.fullname = u'Ukrainian'
    uk.nplurals = '3'
    uk.pluralequation ='(n%10==1 && n%100!=11 ? 0 : n%10>=2 && n%10<=4 && (n%100<10 || n%100>=20) ? 1 : 2)'
    attempt(s,uk)

# Tshivenḓa
# Venda
#    ve.fullname = u'Venda'
#    ve.nplurals = '2'
#    ve.pluralequation ='(n != 1)'
#    ve.specialchars = "ḓṋḽṱ ḒṊḼṰ ṅṄ"

# Vietnamese
    vi = Language("vi")
    vi.fullname = u'Vietnamese'
    vi.nplurals = '1'
    vi.pluralequation ='0'
    attempt(s,vi)

# Wolof
    wo = Language("wo")
    wo.fullname = u'Wolof'
    wo.nplurals = '2'
    wo.pluralequation ='(n != 1)'
    attempt(s,wo)

# Walon
# Walloon
#    wa.fullname = u'Waloon'
#    wa.nplurals = '2'
#    wa.pluralequation ='(n > 1)'

# 简体中文
# Simplified Chinese (China mainland used below, but also used in Singapore and Malaysia)
    zh_CN = Language("zh_CN")
    zh_CN.fullname = u'Chinese (China)'
    zh_CN.nplurals = '1'
    zh_CN.pluralequation ='0'
    zh_CN.specialchars = u"←→↔×÷©…—‘’“”【】《》"
    attempt(s,zh_CN)

# 繁體中文
# Traditional Chinese (Hong Kong used below, but also used in Taiwan and Macau)
    zh_HK = Language("zh_HK")
    zh_HK.fullname = u'Chinese (Hong Kong)'
    zh_HK.nplurals = '1'
    zh_HK.pluralequation ='0'
    zh_HK.specialchars = u"←→↔×÷©…—‘’“”「」『』【】《》"
    attempt(s,zh_HK)

# 繁體中文
# Traditional Chinese (Taiwan used below, but also used in Hong Kong and Macau)
    zh_TW = Language("zh_TW")
    zh_TW.fullname = u'Chinese (Taiwan)'
    zh_TW.nplurals = '1'
    zh_TW.pluralequation ='0'
    zh_TW.specialchars = u"←→↔×÷©…—‘’“”「」『』【】《》"
    attempt(s,zh_TW)

# This is a "language" that gives people access to the (untranslated) template files
    templates = Language("templates")
    templates.fullname = u'Templates'
    attempt(s,templates)

def create_default_users(s):
  admin = User(u"admin")
  admin.name=u"Administrator"
  admin.activated="True"
  admin.passwdhash=md5.new("admin").hexdigest()
  admin.logintype="hash"
  admin.siteadmin=True
  attempt(s,admin)

if __name__ == "__main__":
  main()
