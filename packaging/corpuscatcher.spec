%{!?python_sitelib: %define python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}

Name:           corpuscatcher
Version:        0.1
Release:        1%{?dist}
Summary:        Corpus collection toolset

Group:          Development/Tools
License:        GPLv2+
URL:            http://translate.sourceforge.net/wiki/corpuscatcher/index
Source0:        http://downloads.sourceforge.net/translate/%{name}-%{version}.tar.gz
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

Patch1:          corpuscatcher-sitelib.patch

BuildArch:      noarch
BuildRequires:  python-devel
BuildRequires:  python-mechanize
BuildRequires:  pYsearch


%description
CorpusCatcher is a corpus collection toolset created to facilitate the creation of next-generation spell-checkers by Translate.org.za. 


%prep
%setup -q -n %{name}
%patch1 -p1


%build


%install
rm -rf $RPM_BUILD_ROOT
mkdir -p $RPM_BUILD_ROOT/%{_bindir}
mkdir -p $RPM_BUILD_ROOT/%{python_sitelib}/corpuscatcher
install -m 755 corpus_collect.py $RPM_BUILD_ROOT/%{_bindir}/corpus_collect
install -m 755 clean_corpus.py $RPM_BUILD_ROOT/%{_bindir}/clean_corpus
install -m 755 h2t.py $RPM_BUILD_ROOT/%{python_sitelib}/corpuscatcher/h2t.py
install -m 644 __version__.py $RPM_BUILD_ROOT/%{python_sitelib}/corpuscatcher/__version__.py
touch __init__.py
install -m 644 __init__.py $RPM_BUILD_ROOT/%{python_sitelib}/corpuscatcher/__init__.py


%clean
rm -rf $RPM_BUILD_ROOT


%files
%defattr(-,root,root,-)
%doc README LICENSE
%{_bindir}/*
%{python_sitelib}/corpuscatcher*


%changelog
* Thu Jul 17 2008 Dwayne Bailey <dwayne@translate.org.za> - 0.9.1-1
- Initial packaging
