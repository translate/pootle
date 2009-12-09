%{!?python_sitearch: %define python_sitearch %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib(1)")}

%define pkgname py

Name:           pylib
Version:        0.9.2
Release:        2%{?dist}
Summary:        py lib aims to support an improved development process addressing deployment, versioning, testing and documentation.

Group:          Development/Tools
License:        GPLv2+
URL:            http://codespeak.net/py/dist/index.html
Source0:        http://pypi.python.org/packages/source/p/py/%{pkgname}-%{version}.tar.gz
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

BuildRequires:  python-devel
BuildRequires:  python-setuptools >= 0.6c8


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
%{python_sitearch}/py*


%changelog
* Wed Oct 29 2008 Dwayne Bailey <dwayne@translate.org.za> - 0.9.2-2
- Drop noarch and adjust python_sitelib to _sitearch
- Remove uneeded debug package
- Add python-setuptools as a BuildRequires

* Tue Sep 2 2008 Dwayne Bailey <dwayne@translate.org.za> - 0.9.2-1
- Update to 0.9.2 release
- Add debug package

* Thu Jul 17 2008 Dwayne Bailey <dwayne@translate.org.za> - 0.9.1-1
- Initial packaging
