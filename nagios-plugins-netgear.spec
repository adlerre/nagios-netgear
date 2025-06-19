%global debug_package %{nil}

%define isaix %(test "`uname -s`" = "AIX" && echo "1" || echo "0")
%define islinux %(test "`uname -s`" = "Linux" && echo "1" || echo "0")
%define isx86_64 %(test "`uname -p`" = "x86_64" && echo "1" || echo "0")
%define isredhatfamily %(test -f /etc/redhat-release && echo "1" || echo "0")

%if %{isaix}
	%define _prefix /opt/nagios
%else
    %if %{isx86_64}
	    %define _libexecdir %{_exec_prefix}/lib64/nagios/plugins
	%else
	    %define _libexecdir %{_exec_prefix}/lib/nagios/plugins
	%endif
%endif
%define _sysconfdir /etc/nagios

%define plugin_name check_netgear.py

%define npusr nagios
%define nphome /opt/nagios
%define npgrp nagios

Name:           nagios-plugins-netgear
Version:        0.0.0
Release:        1%{?dist}
Summary:        Nagios Check Command for Netgear Switch
URL:            https://github.com/adlerre/nagios-netgear
Group:          Applications/System
License:        GNU GPLv2+

Source0:        check_netgear.py
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

%if %{isaix}
Prefix: %{_prefix}
%else
Prefix: %{_prefix}/lib/nagios/plugins
%endif
Provides:       %{plugin_name}

Requires:	    python3
Requires:       python3-urllib3
Requires:       python3-rsa

%description

Checks version, temperature, fan and POE power and memory.

%pre
# Create `nagios' group on the system if necessary
%if %{isaix}
lsgroup %{npgrp} > /dev/null 2> /dev/null
if [ $? -eq 2 ] ; then
	mkgroup %{npgrp} || %nnmmsg Unexpected error adding group "%{npgrp}". Aborting install process.
fi
%endif
%if %{islinux}
getent group %{npgrp} > /dev/null 2> /dev/null
if [ $? -ne 0 ] ; then
	groupadd %{npgrp} || %nnmmsg Unexpected error adding group "%{npgrp}". Aborting install process.
fi
%endif

# Create `nagios' user on the system if necessary
%if %{isaix}
lsuser %{npusr} > /dev/null 2> /dev/null
if [ $? -eq 2 ] ; then
	useradd -d %{nphome} -c "%{npusr}" -g %{npgrp} %{npusr} || \
		%nnmmsg Unexpected error adding user "%{npusr}". Aborting install process.
fi
%endif
%if %{islinux}
getent passwd %{npusr} > /dev/null 2> /dev/null
if [ $? -ne 0 ] ; then
	useradd -r -d %{nphome} -c "%{npusr}" -g %{npgrp} %{npusr} || \
		%nnmmsg Unexpected error adding user "%{npusr}". Aborting install process.
fi
%endif

%install
rm -rf $RPM_BUILD_ROOT

install -dm 755 $RPM_BUILD_ROOT%{_libexecdir}
install -pm 644 %{SOURCE0} $RPM_BUILD_ROOT%{_libexecdir}

%files
%defattr(755,%{npusr},%{npgrp})
%{_libexecdir}/%{plugin_name}

%clean
rm -rf $RPM_BUILD_ROOT

%changelog
* Thu Jun 19 2025 René Adler - 1.0.0
- the check command
