%{!?python_sitearch: %define python_sitearch %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib(1)")}

Name:         python-Levenshtein
Summary:      Python extension computing string distances and similarities
Version:      0.10.1
Release:      5%{?dist}

Group:        Development/Libraries
License:      GPLv2+
URL:          http://trific.ath.cx/python/levenshtein/
Source:       http://downloads.sourceforge.net/translate/python-Levenshtein-%{version}.tar.bz2
Source1:      genextdoc.py
BuildRoot:    %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

BuildRequires: python-devel
BuildRequires: python-setuptools-devel

%description
Levenshtein computes Levenshtein distances, similarity ratios, generalized
medians and set medians of Strings and Unicodes.  Because it's implemented
in C, it's much faster than corresponding Python library functions and
methods.


%prep
%setup -q
cp %{SOURCE1} .

%build
CFLAGS="$RPM_OPT_FLAGS" %{__python} -c 'import setuptools; execfile("setup.py")' build
 
%install
rm -rf $RPM_BUILD_ROOT
%{__python} -c 'import setuptools; execfile("setup.py")' install --skip-build --root $RPM_BUILD_ROOT
PYTHONPATH=$PYTHONPATH:$RPM_BUILD_ROOT/%{python_sitearch} %{__python} genextdoc.py Levenshtein

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root,-)
%doc README COPYING NEWS StringMatcher.py Levenshtein.html
%{python_sitearch}/*egg-info
%{python_sitearch}/Levenshtein.so

%changelog
* Thu Mar 27 2008 Dwayne Bailey <dwayne@translate.org.za> - 0.10.1-5
- Build and package *egg-info
- Fix some rpmlint issues

* Thu Feb 14 2008 Dwayne Bailey <dwayne@translate.org.za> - 0.10.1-4
- Add genextdoc.py as Source not Patch

* Wed Jan 30 2008 Dwayne Bailey <dwayne@translate.org.za> - 0.10.1-3
- Some rpmlint fixes
- Fix document generation

* Wed Jan 23 2008 Dwayne Bailey <dwayne@translate.org.za> - 0.10.1-2
- Add missing genextdoc.py to generate usage documentation

* Wed Jan 23 2008 Dwayne Bailey <dwayne@translate.org.za> - 0.10.1-1
- Initial packaging
