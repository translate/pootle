%{!?python_sitelib: %define python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}

%define pkgname py

Name:           pylib
Version:        0.9.2
Release:        1%{?dist}
Summary:        py lib aims to support an improved development process addressing deployment, versioning, testing and documentation.

Group:          Development/Tools
License:        GPLv2+
URL:            http://codespeak.net/py/dist/index.html
Source0:        http://pypi.python.org/packages/source/p/py/%{pkgname}-%{version}.tar.gz
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

BuildArch:      noarch
BuildRequires:  python-devel


%description
Main tools and API:
* py.test introduces to the py.test testing utility.
* py.execnet distributes programs across the net.
* py.magic.greenlet: micro-threads (lightweight in-process concurrent programming)
* py.path: local and subversion Path and Filesystem access
* py.code: High-level access/manipulation of Python code and traceback objects
* py lib scripts describe the scripts contained in the py/bin directory.
* apigen: a new way to generate rich Python API documentation

Support functionality
* py.xml for generating in-memory xml/html object trees
* py.io: Helper Classes for Capturing of Input/Output
* py.log: an alpha document about the ad-hoc logging facilities

%package debug
Summary:        Debug data for %{name} applications.
Group:          Development/Tools
License:        GPLv2+
Requires:       %{name} = %{version}-%{release}

%description debug
The %{name}-debug package contains debug data for specifically the greenlets
application.


%prep
%setup -q -n %{pkgname}-%{version}


%build
%{__python} setup.py build


%install
rm -rf $RPM_BUILD_ROOT
%{__python} setup.py install -O1 --skip-build --root $RPM_BUILD_ROOT


%clean
rm -rf $RPM_BUILD_ROOT


%files
%defattr(-,root,root,-)
%doc py/doc/*
%doc py/LICENSE
%{_bindir}/*
%{python_sitelib}/py*

%files debug
/usr/lib/debug/.build-id/8b/f0be26315769659f345b15c6a33fbaa29c6ead*
/usr/src/debug/py-0.9.2/*
/usr/lib/debug/usr/lib/python2.5/site-packages/py/c-extension/greenlet/greenlet.so.debug


%changelog
* Tue Sep 2 2008 Dwayne Bailey <dwayne@translate.org.za> - 0.9.2-1
- Update to 0.9.2 release
- Add debug package

* Thu Jul 17 2008 Dwayne Bailey <dwayne@translate.org.za> - 0.9.1-1
- Initial packaging
