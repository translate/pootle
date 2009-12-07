%{!?python_sitelib: %define python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}

%define         prerelease ""

Name:           translate-toolkit
Version:        1.2.0
Release:        1%{?dist}
Summary:        Tools to assist with localization

Group:          Development/Tools
License:        GPLv2+
URL:            http://translate.sourceforge.net/wiki/toolkit/index
Source0:        http://downloads.sourceforge.net/translate/%{name}-%{version}.tar.bz2
#Source0:        http://translate.sourceforge.net/snapshots/%{name}-%{version}%{prerelease}/%{name}-%{version}%{prerelease}.tar.bz2
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

Patch0:		translate-poterminology-stoplist.diff

BuildArch:      noarch
BuildRequires:  python-devel
Requires:       python-enchant
Requires:       python-psyco
Requires:       python-Levenshtein
Requires:       python-lxml
Requires:       python-iniparse
Requires:       python-vobject
Requires:       gettext-devel


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

%package devel
Summary:        Development API for %{name} applications
Group:          Development/Tools
License:        GPLv2+
Requires:       %{name} = %{version}-%{release}

%description devel
The %{name}-devel package contains Translate Toolkit API documentation for 
developers wishing to build new tools or reuse the libraries in other tools.


%prep
%setup -q -n %{name}-%{version}%{prerelease}
%patch0 -p1


%build
%{__python} setup.py build


%install
rm -rf $RPM_BUILD_ROOT
%{__python} setup.py install -O1 --skip-build --root $RPM_BUILD_ROOT

# Create the manpages
mkdir -p $RPM_BUILD_ROOT/%{_mandir}/man1
for program in $RPM_BUILD_ROOT/%{_bindir}/*;
do
    case $(basename $program) in
    pocompendium|poen|pomigrate2|popuretext|poreencode|posplit|pocount|poglossary|lookupclient.py)
        ;;
    *)
        LC_ALL=C PYTHONPATH=. $program --manpage \
        >  $RPM_BUILD_ROOT/%{_mandir}/man1/$(basename $program).1 \
        || rm -f $RPM_BUILD_ROOT/%{_mandir}/man1/$(basename $program).1
        ;;
    esac
done

# remove documentation files from site-packages
rm -r $RPM_BUILD_ROOT/%{python_sitelib}/translate/doc
rm $RPM_BUILD_ROOT/%{python_sitelib}/translate/{COPYING,ChangeLog,LICENSE,README}
rm $RPM_BUILD_ROOT/%{python_sitelib}/translate/{convert,filters,tools}/TODO
rm $RPM_BUILD_ROOT/%{python_sitelib}/translate/misc/README

# Move data files to /usr/share
mkdir  $RPM_BUILD_ROOT/%{_datadir}/translate-toolkit
mv $RPM_BUILD_ROOT/%{python_sitelib}/translate/share/stoplist* $RPM_BUILD_ROOT/%{_datadir}/translate-toolkit


%clean
rm -rf $RPM_BUILD_ROOT


%files
%defattr(-,root,root,-)
%doc translate/doc/user/toolkit-[a-z]*
%doc translate/ChangeLog translate/COPYING translate/README
%{_bindir}/*
%{_mandir}/man1/*
%{_datadir}/translate-toolkit
%{python_sitelib}/translate*
%exclude %{_bindir}/*.pyc
%exclude %{_bindir}/*.pyo

%files devel
%doc translate/doc/api/*


%changelog
* Mon Oct 6 2008 Dwayne Bailey <dwayne@translate.org.za> - 1.2.0-1.fc9
- Update to 1.2.0 final
- Include stoplist-en and adjust poterminology to read it from the 
  /usr/share/ location

* Tue Sep 30 2008 Dwayne Bailey <dwayne@translate.org.za> - 1.2.0-0.3.rc1.fc9
- Update to 1.2.0-rc1
- Include ical2po dependencies

* Tue Aug 26 2008 Dwayne Bailey <dwayne@translate.org.za> - 1.2-0.2.beta2.fc9
- Update to 1.2-beta2

* Mon Aug 25 2008 Dwayne Bailey <dwayne@translate.org.za> - 1.2-0.1.beta1.fc9
- Update to 1.2-beta1

* Tue Jun 3 2008 Dwayne Bailey <dwayne@translate.org.za> - 1.1.1-1.fc9
- Rebuild for fc9

* Thu Mar 27 2008 Dwayne Bailey <dwayne@translate.org.za> - 1.1.1-1.fc8
- Update to official 1.1.1 release
- Patches to fix internal project rename wordforge -> locamotion
- Use included API documentation

* Wed Mar 12 2008 Dwayne Bailey <dwayne@translate.org.za> - 1.1.1-0.4.rc4.fc8
- Update to 1.1.1rc4

* Wed Mar 5 2008 Dwayne Bailey <dwayne@translate.org.za> - 1.1.1-0.3.rc3.fc8
- Add devel package to include generated Translate Toolkit API documentation

* Mon Feb 25 2008 Dwayne Bailey <dwayne@translate.org.za> - 1.1.1-0.2.rc3.fc8
- Update to 1.1.1rc3
- Remove ini2po patch

* Thu Feb 14 2008 Dwayne Bailey <dwayne@translate.org.za> - 1.1.1-0.1.rc2.fc8
- Update to 1.1.1rc2

* Thu Feb 14 2008 Dwayne Bailey <dwayne@translate.org.za> - 1.1.0-1.fc8
- Update to 1.1.0
- Remove old ElementTree patch
- Add dependencies: python-Levenshtein, python-lxml, python-iniparse, 
  gettext-devel
- Package ini2po

* Tue Jan 22 2008 Dwayne Bailey <dwayne@translate.org.za> - 1.0.1-4.fc8
- Remove python-Levenshtein dependency: rhbz#429882 and rhbz#430887

* Tue Jan 22 2008 Caius Chance <cchance@redhat.com> - 1.0.1-3.fc8
- Resolves: rhbz#315021
 - Update license field to GPLv2+.
 - Update to 1.0.1 with changes from Dwayne Bailey.

* Thu Dec 20 2007 Dwayne Bailey <dwayne@translate.org.za> - 1.0.1-2
- Create man pages

* Thu Dec 19 2007 Dwayne Bailey <dwayne@translate.org.za> - 1.0.1-1
- Update to upstream 1.0.1
- Update patch for Python 2.5 ElementTree
- Cleanup the doc installation

* Sat May 05 2007 Roozbeh Pournader <roozbeh@farsiweb.info> - 0.11-1
- Update to upstream 0.11, adding HTML documentation

* Tue Jan 09 2007 Roozbeh Pournader <roozbeh@farsiweb.info> - 0.10.1-4
- Patch to use Python 2.5's built-in ElementTree

* Sat Dec 30 2006 Roozbeh Pournader <roozbeh@farsiweb.info> - 0.10.1-3
- Rebuild to fix dependency problem

* Sat Dec 09 2006 Roozbeh Pournader <roozbeh@farsiweb.info> - 0.10.1-2
- Rebuild for Python 2.5

* Thu Nov 09 2006 Roozbeh Pournader <roozbeh@farsiweb.info> - 0.10.1-1
- Update to upstream 0.10.1
- Cleanup based on latest Python packaging guidelines

* Wed Nov 08 2006 Roozbeh Pournader <roozbeh@farsiweb.info> - 0.8-2
- Rebuild to get into Rawhide

* Mon Feb 20 2006 Roozbeh Pournader <roozbeh@farsiweb.info> - 0.8-1
- Update to final 0.8

* Sun Feb 19 2006 Roozbeh Pournader <roozbeh@farsiweb.info> - 0.8-0.10.rc6
- Fix a typo in po2dtd that made po2moz fail

* Tue Feb 14 2006 Roozbeh Pournader <roozbeh@farsiweb.info> - 0.8-0.9.rc6
- Rebuild for Fedora Extras 5

* Tue Feb 07 2006 Roozbeh Pournader <roozbeh@farsiweb.info> - 0.8-0.8.rc6
- Require python-enchant for spellchecking support in pofilter

* Sat Feb 04 2006 Roozbeh Pournader <roozbeh@farsiweb.info> - 0.8-0.7.rc6
- Rebuild

* Sat Feb 04 2006 Roozbeh Pournader <roozbeh@farsiweb.info> - 0.8-0.6.rc6
- Update to 0.8rc6

* Sat Jan 21 2006 Roozbeh Pournader <roozbeh@farsiweb.info> - 0.8-0.5.rc5
- Use sed instead of dos2unix

* Mon Jan 09 2006 Roozbeh Pournader <roozbeh@farsiweb.info> - 0.8-0.4.rc5
- Own forgotten subdirectories

* Mon Jan 09 2006 Roozbeh Pournader <roozbeh@farsiweb.info> - 0.8-0.3.rc5
- Fix the jToolkit requirement

* Sun Jan 08 2006 Roozbeh Pournader <roozbeh@farsiweb.info> - 0.8-0.2.rc5
- Add %%{?dist} tag

* Sat Jan 07 2006 Roozbeh Pournader <roozbeh@farsiweb.info> - 0.8-0.1.rc5
- Initial packaging
