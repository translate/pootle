%{!?python_sitelib: %define python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}

%define         fullname Pootle

Name:           pootle
Version:        1.2.0
Release:        1%{?dist}
Summary:        Localization and translation management web application

Group:          Development/Tools
License:        GPLv2+
URL:            http://translate.sourceforge.net/wiki/pootle/index
Source:        http://downloads.sourceforge.net/translate/%{fullname}-%{version}.tar.bz2
#Source:         http://translate.sourceforge.net/snapshots/%{fullname}-%{version}-beta2/%{fullname}-%{version}%{prerelease}.tar.bz2
Source1:        pootle-initscript
Source2:        pootle-logrotate
Source3:        pootle-sysconfig
Source4:        run_pootle.sh
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

Patch1:         pootle-1.2.0-fixes.patch

BuildArch:      noarch
BuildRequires:  python-devel
Requires:       translate-toolkit >= 1.2
Requires:       jToolkit
Requires:       python-kid
Requires:       iso-codes
Requires(pre): shadow-utils
# Options
# Xapian, PyLucene



%description
A web application for managing the translation of Gettext PO and XLIFF files.

%prep
%setup -q -n %{fullname}-%{version}
%patch1 -p1


%build
%{__python} pootlesetup.py build


%install
rm -rf $RPM_BUILD_ROOT
%{__python} pootlesetup.py install -O1 --skip-build --root $RPM_BUILD_ROOT

# Create the manpages
mkdir -p $RPM_BUILD_ROOT/%{_mandir}/man1
for program in $RPM_BUILD_ROOT/%{_bindir}/*;
do
    case $(basename $program) in
    PootleServer)
        ;;
    *)
        LC_ALL=C PYTHONPATH=. $program --manpage \
        >  $RPM_BUILD_ROOT/%{_mandir}/man1/$(basename $program).1 \
        || rm -f $RPM_BUILD_ROOT/%{_mandir}/man1/$(basename $program).1
        ;;
    esac
done

# remove documentation files from site-packages
rm $RPM_BUILD_ROOT/%{python_sitelib}/Pootle/{COPYING,ChangeLog,LICENSE,README}
rm $RPM_BUILD_ROOT/%{python_sitelib}/Pootle/test_*
install -d $RPM_BUILD_ROOT/usr/sbin $RPM_BUILD_ROOT/usr/share/pootle/ $RPM_BUILD_ROOT/usr/share/pootle/html $RPM_BUILD_ROOT/usr/share/pootle/templates $RPM_BUILD_ROOT/var/lib/pootle $RPM_BUILD_ROOT/etc/pootle
install $RPM_BUILD_ROOT/usr/bin/PootleServer $RPM_BUILD_ROOT/usr/sbin
rm $RPM_BUILD_ROOT/usr/bin/PootleServer
mv $RPM_BUILD_ROOT/%{python_sitelib}/Pootle/html $RPM_BUILD_ROOT/usr/share/pootle
install $RPM_BUILD_ROOT/%{python_sitelib}/Pootle/templates/*.html $RPM_BUILD_ROOT/usr/share/pootle/templates
rm  $RPM_BUILD_ROOT/%{python_sitelib}/Pootle/templates/*.html
mv $RPM_BUILD_ROOT/%{python_sitelib}/Pootle/po/pootle $RPM_BUILD_ROOT/var/lib/pootle
install $RPM_BUILD_ROOT/%{python_sitelib}/Pootle/*.prefs $RPM_BUILD_ROOT/etc/pootle
install -d $RPM_BUILD_ROOT/var/cache/pootle
install -d $RPM_BUILD_ROOT/var/log/pootle
install $RPM_SOURCE_DIR/pootle-initscript -D $RPM_BUILD_ROOT/etc/rc.d/init.d/pootle
install $RPM_SOURCE_DIR/pootle-logrotate -D $RPM_BUILD_ROOT/etc/logrotate.d/pootle
install $RPM_SOURCE_DIR/pootle-sysconfig -D $RPM_BUILD_ROOT/etc/sysconfig/pootle
install $RPM_SOURCE_DIR/run_pootle.sh -D $RPM_BUILD_ROOT/usr/sbin


%clean
rm -rf $RPM_BUILD_ROOT

%pre
%define groupname %{name}
%define username %{name}

getent group %{groupname} >/dev/null || groupadd -r %{groupname}
getent passwd %{username} >/dev/null || \
useradd -r -g %{groupname} -d /var/lib/pootle -s /sbin/nologin \
-c "Pootle daemon" %{username}
exit 0

%post
chown -R pootle.pootle /var/lib/pootle
chmod -R g+w /var/lib/pootle


%files
%defattr(-,root,root,-)
%doc Pootle/{COPYING,ChangeLog,README}
%{_bindir}/*
%{_sbindir}/*
%{_mandir}/man1/*
%config /etc/pootle
%config /etc/sysconfig/pootle
%{python_sitelib}/Pootle*
/usr/share/pootle
/var/lib/pootle
%dir /var/cache/pootle
%dir /var/log/pootle
/etc/rc.d/init.d/pootle
/etc/logrotate.d/pootle


%changelog
* Mon Oct 6 2008 Dwayne Bailey <dwayne@translate.org.za> - 1.2.0-1.fc9
- Update to final 1.2.0 release

* Tue Sep 30 2008 Dwayne Bailey <dwayne@translate.org.za> - 1.2.0-0.5.rc1.fc9
- Update to RC1

* Tue Sep 2 2008 Dwayne Bailey <dwayne@translate.org.za> - 1.2.0-0.4.beta2.fc9
- Create run_pootle.sh wrapper for server

* Wed Aug 27 2008 Dwayne Bailey <dwayne@translate.org.za> - 1.2.0-0.3.beta2.fc9
- Create man pages
- Rebuild with a refreshed tarball that contains jquery

* Wed Aug 27 2008 Dwayne Bailey <dwayne@translate.org.za> - 1.2.0-0.2.beta2.fc9
- Update to 1.2.0-beta2
- Fix initscript installation location

* Sun Aug 24 2008 Dwayne Bailey <dwayne@translate.org.za> - 1.2.0-0.1.beta1.fc9
- Build for 1.2.0-beta1 release
- Create initscripts, sysconfig; create proper logging; configure stats database

* Thu Feb 14 2008 Dwayne Bailey <dwayne@translate.org.za> - 1.0.2-1.fc9
- Rebuild for fc9

* Thu Feb 14 2008 Dwayne Bailey <dwayne@translate.org.za> - 1.0.2-1.fc8
- Initial packaging
