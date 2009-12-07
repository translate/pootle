%{!?python_sitelib: %define python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}

Name:           pYsearch
Version:        3.1
Release:        1%{?dist}
Summary:        Python API for the Yahoo Search Webservices API

Group:          Development/Tools
License:        GPLv2+
URL:            http://sourceforge.net/projects/pysearch/
Source0:        http://downloads.sourceforge.net/pysearch/%{name}-%{version}.tar.gz
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

BuildArch:      noarch
BuildRequires:  python-devel


%description
pYsearch implements a Python API for the Yahoo Search Webservices API. It provides an object orientated 
abstraction of the web services, with emphasis on ease of use and extensibility.

%prep
%setup -q -n %{name}-%{version}


%build
%{__python} setup.py build


%install
rm -rf $RPM_BUILD_ROOT
%{__python} setup.py install -O1 --skip-build --root $RPM_BUILD_ROOT


%clean
rm -rf $RPM_BUILD_ROOT


%files
%defattr(-,root,root,-)
%doc ChangeLog README NEWS docs
%{python_sitelib}/yahoo/*
%{python_sitelib}/pYsearch*


%changelog
* Thu Jul 17 2008 Dwayne Bailey <dwayne@translate.org.za> - 3.1-1
- Initial packaging
