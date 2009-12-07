%{!?python_sitelib: %define python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}

Name:           virtaal
Version:        0.2
Release:        3%{?dist}
Summary:        Localization and translation editor

Group:          Development/Tools
License:        GPLv2+
URL:            http://translate.sourceforge.net/wiki/virtaal/index
Source0:        http://downloads.sourceforge.net/translate/%{name}-%{version}.tar.bz2
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

Patch0:         virtaal-0.2-setup_drop_MO_generation.patch

BuildArch:      noarch
BuildRequires:  python
BuildRequires:  python-devel
BuildRequires:  gettext
BuildRequires:  intltool
Requires:       translate-toolkit >= 1.2
Requires:       pygtk2
Requires:       pygtk2-libglade
Requires:       python-lxml
Requires:       gnome-python2-gtkspell
Requires:       xdg-utils


%description
A program for Computer Aided Translation (CAT) built on the Translate Toolkit.

Virtaal includes features that allow a localizer to work effectively including:
syntax highlighting, autocomplete and autocorrect.  Showing only 
the data that is needed through its simple and effective user interface it
ensures that you can focus on the translation task straight away.

By building on the Translate Toolkit, Virtaal is able to edit any of the
following formats: XLIFF, Gettext PO and .mo, Qt .ts, .qph and .qm, Wordfast 
TM, TMX, TBX.  By using the Translate Toolkit converters a translator can edit:
OpenOffice.org SDF, Java (and Mozilla) .properties and Mozilla DTD.
 

%prep
%setup -q -n %{name}-%{version}
%patch0 -p1

%build
%{__python} setup.py build
./maketranslations %{name}
pushd po
for po in $(ls *.po | egrep -v de_DE)
do
    mkdir -p locale/$(basename $po .po)/LC_MESSAGES/
    msgfmt $po --output-file=locale/$(basename $po .po)/LC_MESSAGES/%{name}.mo
done
popd


%install
rm -rf %{buildroot}
%{__python} setup.py install -O1 --skip-build --install-data=/usr --root %{buildroot}

desktop-file-install                                     \
   --delete-original                                     \
   --dir=%{buildroot}%{_datadir}/applications            \
   %{buildroot}%{_datadir}/applications/%{name}.desktop
cp -rp po/locale %{buildroot}%{_datadir}/
%find_lang %{name}


%post
update-desktop-database &> /dev/null || :
update-mime-database %{_datadir}/mime &> /dev/null || :
touch --no-create %{_datadir}/icons/hicolor
if [ -x %{_bindir}/gtk-update-icon-cache ]; then
  %{_bindir}/gtk-update-icon-cache --quiet %{_datadir}/icons/hicolor || :
fi


%postun
update-desktop-database &> /dev/null || :
update-mime-database %{_datadir}/mime &> /dev/null || :
touch --no-create %{_datadir}/icons/hicolor
if [ -x %{_bindir}/gtk-update-icon-cache ]; then
  %{_bindir}/gtk-update-icon-cache --quiet %{_datadir}/icons/hicolor || :
fi


%clean
rm -rf %{buildroot}


%files -f %{name}.lang
%defattr(-,root,root,-)
%doc README LICENSE po/*.pot
%{_bindir}/*
%{_datadir}/applications/*
%{_datadir}/mime/packages/*
%{_datadir}/virtaal
%{_datadir}/icons/*
%{python_sitelib}/*


%changelog
* Sun Dec 28 2008 Dwayne Bailey <dwayne@translate.org.za> - 0.2-3
- Drop BuildRequires: desktop-file-utils

* Sat Dec 6 2008 Dwayne Bailey <dwayne@translate.org.za> - 0.2-2
- Cleanups from package review

* Thu Oct 16 2008 Dwayne Bailey <dwayne@translate.org.za> - 0.2-1
- Build for final 0.2 release
- Add pygtk2-libglade dependency

* Thu Oct 2 2008 Dwayne Bailey <dwayne@translate.org.za> - 0.2-0.3.rc1
- Rebuild after tarball restructuring

* Wed Oct 1 2008 Dwayne Bailey <dwayne@translate.org.za> - 0.2-0.2.rc1
- Fix file locations

* Wed Oct 1 2008 Dwayne Bailey <dwayne@translate.org.za> - 0.2-0.1.rc1
- Update to RC1

* Sat Sep 20 2008 Dwayne Bailey <dwayne@translate.org.za> - 0.1-12
- Include LICENSE

* Thu Sep 11 2008 Dwayne Bailey <dwayne@translate.org.za> - 0.1-11
- Update for various file moves.
- Package virtaal.pot and gtk+-lite.pot
- Exclude the de_DE.mo debug translations

* Sat Jul 26 2008 Dwayne Bailey <dwayne@translate.org.za> - 0.1-10
- Package autocorrect files

* Thu Jul 24 2008 Dwayne Bailey <dwayne@translate.org.za> - 0.1-9
- Rebuild after upstream data location changes

* Tue Jun 3 2008 Dwayne Bailey <dwayne@translate.org.za> - 0.1-8
- Rebuild for fc9

* Fri May 9 2008 Dwayne Bailey <dwayne@translate.org.za> - 0.1-8
- Add xdg-utils as a requirement as we are using xdg-open

* Wed May 7 2008 Dwayne Bailey <dwayne@translate.org.za> - 0.1-7
- Adjust to changes in source package

* Wed Apr 30 2008 Dwayne Bailey <dwayne@translate.org.za> - 0.1-6
- Adjust to changes in source package

* Thu Apr 17 2008 Dwayne Bailey <dwayne@translate.org.za> - 0.1-5
- Install icon

* Thu Apr 17 2008 Dwayne Bailey <dwayne@translate.org.za> - 0.1-4
- Build translatable files using intltool

* Mon Apr 14 2008 Dwayne Bailey <dwayne@translate.org.za> - 0.1-3
- Install translations

* Sat Apr 12 2008 Dwayne Bailey <dwayne@translate.org.za> - 0.1-2
- Executable s/run_virtaal.py/virtaal/
- Remove .glade movement, ./setup.py install it correctly now
- Install .desktop, locale, mime files
- Update desktop- and mime-database

* Sat Apr 5 2008 Dwayne Bailey <dwayne@translate.org.za> - 0.1-1
- Initial packaging
