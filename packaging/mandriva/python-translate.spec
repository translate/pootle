%define pname		translate
%define upstream_name	%{pname}-toolkit

Name:		python-%{pname}
Version:	1.5.1
Release:	%mkrel 1

Summary:	Software localization toolkit
License:	GPLv2+
Group:		Development/Python
URL:		http://translate.sourceforge.net/
Source0:	http://downloads.sourceforge.net/translate/%{upstream_name}-%{version}.tar.bz2

BuildArch:	noarch
Buildrequires:	rpm-mandriva-setup >= 1.23
Buildrequires:	rpm-helper >= 0.16
BuildRoot:	%{_tmppath}/%{name}-%{version}-%{release}-buildroot

%py_requires -d

Requires:	python-lxml
Requires(post):	rpm-helper >= 0.16
Requires(postun): rpm-helper >= 0.16

Suggests:	python-psyco
Suggests:	python-simplejson
Suggests:	python-levenshtein
Suggests:	python-enchant
Suggests:	python-vobject
Suggests:	python-iniparse
Suggests:	gaupol

Provides:	%{upstream_name} = %{version}-%{release}


%description
A set of tools for managing localization via Gettext PO or XLIFF format files.
 
Including:
  * Convertors: convert from various formats to PO or XLIFF
  * Formats:
    * Core localization formats - XLIFF and Gettext PO
    * Other localization formats - TMX, TBX, Qt Linguist (.ts), 
      Java .properties, Wordfast TM
    * Compiled formats: Gettext MO, Qt .qm
    * Other formats - text, HTML, CSV, INI, wiki (MediaWiki, DokuWiki), iCal
    * Specialised - OpenOffice.org GSI/SDF, PHP,
      Mozilla (.dtd, .properties, etc)
  * Tools: count, search, debug, segment and extract terminology from
    localization files.
  * Checkers: validate translations with over 46 checks


%prep
%setup -q -n %{upstream_name}-%{version}

%build
./setup.py build

%install
rm -rf %{buildroot}
./setup.py install --root=%{buildroot}

%clean
rm -rf %{buildroot}

%files
%defattr(-,root,root)
%doc %{pname}/README
%{_bindir}/*
%{py_puresitedir}/%{pname}
%{py_puresitedir}/*.egg-info


%changelog
* Fri Nov 27 2009 Alaa Abd El Fattah <alaa@translate.org.za> 1.5.1-1mdv2010.0
- update to new version 1.5.1

* Sat Nov 07 2009 Frederik Himpe <fhimpe@mandriva.org> 1.4.1-1mdv2010.1
+ Revision: 462187
- update to new version 1.4.1

* Tue Aug 11 2009 Frederik Himpe <fhimpe@mandriva.org> 1.4.0-1mdv2010.0
+ Revision: 415157
- update to new version 1.4.0

  + Per Øyvind Karlsen <peroyvind@mandriva.org>
    - add a suggests on 'python-levenshtein'

* Sat May 23 2009 Per Øyvind Karlsen <peroyvind@mandriva.org> 1.3.0-2mdv2010.0
+ Revision: 378867
- add dependency on python-lxml (required by at least pretranslate..)

* Fri Feb 13 2009 Frederik Himpe <fhimpe@mandriva.org> 1.3.0-1mdv2009.1
+ Revision: 340122
- update to new version 1.3.0

* Wed Jan 14 2009 Funda Wang <fundawang@mandriva.org> 1.2.1-1mdv2009.1
+ Revision: 329483
- add provides
- New version 1.2.1

* Sun Dec 28 2008 Funda Wang <fundawang@mandriva.org> 1.2.0-2mdv2009.1
+ Revision: 320351
- rebuild for new python

* Mon Oct 20 2008 Funda Wang <fundawang@mandriva.org> 1.2.0-1mdv2009.1
+ Revision: 295683
- New version 1.2.0

* Mon Oct 20 2008 Funda Wang <fundawang@mandriva.org> 1.0.1-5mdv2009.1
+ Revision: 295682
- should use --root rather than --prefix

* Fri Aug 01 2008 Thierry Vignaud <tvignaud@mandriva.com> 1.0.1-4mdv2009.0
+ Revision: 259837
- rebuild

* Fri Jul 25 2008 Thierry Vignaud <tvignaud@mandriva.com> 1.0.1-3mdv2009.0
+ Revision: 247701
- rebuild

* Thu Jan 17 2008 Olivier Blin <oblin@mandriva.com> 1.0.1-1mdv2008.1
+ Revision: 154232
- 1.0.1

* Wed Jan 02 2008 Olivier Blin <oblin@mandriva.com> 0.10.1-1mdv2008.1
+ Revision: 140738
- restore BuildRoot

  + Thierry Vignaud <tvignaud@mandriva.com>
    - kill re-definition of %%buildroot on Pixel's request


* Fri Jan 12 2007 Olivier Blin <oblin@mandriva.com> 0.10.1-1mdv2007.0
+ Revision: 107921
- buildrequires python-devel
- initial python-translate release
- Create python-translate

