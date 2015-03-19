%define name moin
%define version 1.9.8
%define release 1
#Upgrade Path Example:
#     moin-1.3-0.1.beta1
#         Patched
#     moin-1.3-0.2.beta1
#         Move to beta2
#     moin-1.3-0.3.beta2
#         Move to beta3 and simultaneously patch
#     moin-1.3-0.4.beta3
#         Patched again
#     moin-1.3-0.5.beta3
#         Move to rc1
#     moin-1.3-0.6.rc1
#         Move to rc2
#     moin-1.3-0.7.rc2
#         Move to "final"
#     moin-1.3-1
#         Patched
#     moin-1.3-2

Name: %{name}
Version: %{version}
Release: %{release}
Source0: %{name}-%{version}.tar.gz
Summary:        MoinMoin Wiki engine

Group:          Applications/Internet
License:        GPL
URL:            http://moinmo.in/
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

BuildArchitectures: noarch
BuildRequires:  python-devel
Requires:       python >= 2.5

%description

A WikiWikiWeb is a collaborative hypertext environment, with an
emphasis on easy access to and modification of information. MoinMoin
is a Python WikiClone that allows you to easily set up your own wiki,
only requiring a Python installation. 

%prep
%setup
echo $RPM_BUILD_ROOT

%build
python setup.py build

%install
python setup.py install --root=$RPM_BUILD_ROOT --record=INSTALLED_FILES

%clean
rm -rf $RPM_BUILD_ROOT

#%files -f INSTALLED_FILES   # Wrong: Installed files contains directories also
# This lets rpmbuild complain about Files listet twice.
# A Good explanation is here: "http://www.wideopen.com/archives/rpm-list/2001-February/msg00081.html
%files
%defattr(-,root,root)
/usr
%doc  README docs/CHANGES docs/INSTALL.html docs/UPDATE.html docs/licenses/COPYING

%changelog
* Sun Jan  5 2014 Thomas Waldmann
- Raised requirement to Python 2.5

* Sun Feb 15 2009 Thomas Waldmann
- Raised requirement to Python 2.4
- Removed references to Python 1.5
- Fixed doc files.

* Thu Jun  8 2006 Johannes Poehlmann
- Fix RPM build errror "Files listet twice" 
  Replaced files list and just package all of /usr.

* Fri Mar 05 2004 Florian Festi
- Initial RPM release.

