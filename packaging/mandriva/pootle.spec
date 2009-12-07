%define upstream_name		Pootle
%define upstream_version	2.0.0-rc2

Name:		pootle
Version:	2.0.0
Release:	%mkrel 0.rc2.1

Summary:	Localization and translation management web application
License:	GPLv2+
Group:		Development/Other
URL:		http://translate.sourceforge.net/wiki/pootle/index
Source0:	http://translate.sourceforge.net/snapshots/%{upstream_name}-%{upstream_version}/%{upstream_name}-%{upstream_version}.tar.bz2
Patch0:		pootle-2.0-optimal-settings.patch

BuildArch:	noarch
BuildRequires:	rpm-mandriva-setup >= 1.23
BuildRequires:	rpm-helper >= 0.16
BuildRoot:	%{_tmppath}/%{name}-%{version}-%{release}-buildroot

%py_requires -d
Requires(post):	rpm-helper >= 0.16
Requires(postun): rpm-helper >= 0.16
Requires(pre):	apache-conf >= 2.0.54
Requires(pre):	memcached
Requires:	python-translate >= 1.5.0
Requires:	python-django
Requires:	apache-mod_wsgi
Requires:	python-memcached

Suggests:	python-lxml
Suggests:	python-levenshtein
Suggests:	iso-codes
Suggests:	unzip
Suggests:	xapian-bindings-python
Suggests:	python-mysql
Suggests:	mysqlserver


%description
Pootle is a web application for distributed or crowdsourced translation.

It's features include::
  * Translation of Gettext PO and XLIFF files.
  * Submitting to remote version control systems (VCS).
  * Managing groups of translators
  * Online webbased or offline translation
  * Quality checks


%prep
%setup -q -n %{upstream_name}-%{upstream_version}
%patch0 -p2

%build
%{__python} setup.py build

%install
%{__rm} -rf %{buildroot}
%{__python} setup.py install -O1 --root %{buildroot}

%{__install} -d -m 755 %{buildroot}%{_var}/www/%{name}
%{__cp} %{buildroot}%{_docdir}/%{name}/wsgi.py %{buildroot}%{_var}/www/%{name}

%{__install} -d -m 755 %{buildroot}%{webappconfdir}
cat >> %{buildroot}%{webappconfdir}/%{name}.conf <<EOF
WSGIScriptAlias /%{name} %{_var}/www/%{name}/wsgi.py
<Directory %{_var}/www/%{name}>
    Order deny,allow
    Allow from all
</Directory>

Alias /%{name}/html %{_datadir}/%{name}/html
<Directory "%{_datadir}/%{name}/html">
    Order deny,allow
    Allow from all
</Directory>

Alias /%{name}/export %{_var}/lib/%{name}/po
<Directory "%{_var}/lib/%{name}/po">
    Order deny,allow
    Allow from all
</Directory>
EOF

%clean
rm -rf %{buildroot}

%post
if [ ! -f %{_var}/lock/subsys/memcached ]; then
    %{__service} memcached start
fi
%{_post_webapp}

%postun
%{_postun_webapp}


%files
%defattr(-,root,root)
%{py_puresitedir}/pootle
%{py_puresitedir}/pootle_app
%{py_puresitedir}/pootle_store
%{py_puresitedir}/pootle_notifications
%{py_puresitedir}/pootle_autonotices
%{py_puresitedir}/pootle_misc
%{py_puresitedir}/djblets
%{py_puresitedir}/profiles
%{py_puresitedir}/registration
%{py_puresitedir}/*.egg-info

%{_datadir}/%{name}/html
%{_datadir}/%{name}/templates
%{_datadir}/%{name}/mo

%{_bindir}/PootleServer
%{_bindir}/updatetm
%{_bindir}/import_pootle_prefs 

%attr(0755,apache,apache) %{_var}/lib/%{name}
%{_var}/www/%{name}

%config(noreplace) %{_sysconfdir}/%{name}/localsettings.py
%config(noreplace) %{_webappconfdir}/%{name}.conf
%doc %{_docdir}/%{name}/*


%changelog
* Fri Nov 27 2009 Alaa Abd El Fattah <alaa@translate.org.za> 2.0.0-0.rc2.1mdv2010.0
- first mandriva package since move to Django
