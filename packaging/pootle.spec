%{!?python_sitelib: %define python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}

Name:           pootle
Version:        1.1.0
Release:        0.1.rc1%{?dist}
Summary:        Localization web server

Group:          Development/Tools
License:        GPLv2+
URL:            http://translate.sourceforge.net/wiki/pootle/index
#Source:        http://downloads.sourceforge.net/translate/%{name}-%{version}.tar.bz2
Source:         http://translate.sourceforge.net/snapshots/%{name}-%{version}rc1/%{name}-%{version}rc1.tar.bz2
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

BuildArch:      noarch
BuildRequires:  python-devel
Requires:       translate-toolkit
Requires:       python-jtoolkit
Requires:       python-kid
Requires:       iso-codes
Requires:       PyLucene


%description
A webserver for managing the translation of Gettext PO and XLIFF files.

%prep
%setup -q -n %{name}-%{version}rc1


%build
%{__python} pootlesetup.py build


%install
rm -rf $RPM_BUILD_ROOT
%{__python} pootlesetup.py install -O1 --skip-build --root $RPM_BUILD_ROOT

# remove documentation files from site-packages
rm $RPM_BUILD_ROOT/%{python_sitelib}/Pootle/{COPYING,ChangeLog,LICENSE,README}
rm $RPM_BUILD_ROOT/%{python_sitelib}/Pootle/test_*
mkdir -p $RPM_BUILD_ROOT/usr/sbin
mv $RPM_BUILD_ROOT/usr/bin/PootleServer $RPM_BUILD_ROOT/usr/sbin
mkdir -p $RPM_BUILD_ROOT/usr/share/pootle/
mv $RPM_BUILD_ROOT/%{python_sitelib}/Pootle/html $RPM_BUILD_ROOT/usr/share/pootle/
mv $RPM_BUILD_ROOT/%{python_sitelib}/Pootle/templates $RPM_BUILD_ROOT/usr/share/pootle/
mkdir -p $RPM_BUILD_ROOT/var/lib/pootle/
mv $RPM_BUILD_ROOT/%{python_sitelib}/Pootle/po $RPM_BUILD_ROOT/var/lib/pootle
mkdir -p $RPM_BUILD_ROOT/etc/pootle/
mv $RPM_BUILD_ROOT/%{python_sitelib}/Pootle/*.prefs $RPM_BUILD_ROOT/etc/pootle


%clean
rm -rf $RPM_BUILD_ROOT


%files
%defattr(-,root,root,-)
%doc Pootle/{COPYING,ChangeLog,LICENSE,README}
%{_bindir}/*
%{_sbindir}/*
#%{_mandir}/man1/*
#%exclude %{_bindir}/*.pyc
#%exclude %{_bindir}/*.pyo
%config /etc/pootle
%{python_sitelib}/Pootle*/*.py*
%{python_sitelib}/Pootle*/tools/*.py*
/usr/share/pootle
/var/lib/pootle


%changelog
* Thu Feb 14 2008 Dwayne Bailey <dwayne@translate.org.za> - 1.0.2-1.fc8
- Initial packaging
