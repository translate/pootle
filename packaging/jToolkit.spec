%{!?python_sitelib: %define python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}

Name:           jToolkit
Version:        0.7.8
Release:        2%{?dist}
Summary:        Web application framework

Group:          Development/Python
License:        GPL
Url:            http://jtoolkit.sourceforge.net/
Source0:        http://jtoolkit.sourceforge.net/snapshots/jToolkit-0.7.8/%{name}-%{version}.tar.gz
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

Patch0:         jToolkit-sre-removal.patch

BuildArch:      noarch
BuildRequires:  python-devel


%description
jToolkit is a Python web application framework built on modpython and
Apache. It can also run in standalone mode using its own builtin HTTP
server.

It is aimed at dynamically generated pages rather than mostly-static
pages (for which there are templating solutions). Pages can be
produced using a variety of widgets or a new templating system. It
handles sessions and database connections.


%prep
%setup -q -n %{name}-%{version}
%patch0 -p1


%build
%{__python} jToolkitSetup.py build


%install
rm -rf $RPM_BUILD_ROOT
%{__python} jToolkitSetup.py install -O1 --skip-build --root $RPM_BUILD_ROOT 


%clean
rm -rf $RPM_BUILD_ROOT


%files
%defattr(-,root,root,-)
%doc ChangeLog COPYING
%{python_sitelib}/jToolkit*


%changelog
* Tue Jun 3 2008 Dwayne Bailey <dwayne@translate.org.za> - 0.7.8-2.fc9
- Rebuild for fc9
- Package Python egg

* Wed May 07 2008 Dwayne Bailey <dwayne@translate.org.za> - 0.7.8-2
- Remove imports of deprecated sre module

* Wed May 07 2008 Dwayne Bailey <dwayne@translate.org.za> - 0.7.8-1
- Initial packaging
