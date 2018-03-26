%define debug_package %{nil}
%define __jar_repack %{nil}
%global __provides_exclude ^osgi.*$
%global __requires_exclude ^osgi.*$

%global jira_install /opt/atlassian/jira
%global jira_conf %{_sysconfdir}%{jira_install}
%global jira_home %{_localstatedir}/atlassian/application-data/jira
%global jira_log %{_localstatedir}/log/atlassian/jira
%global jira_run %{_rundir}/atlassian/jira

%global jira_systemd_envfile %{_sysconfdir}/sysconfig/%{name}

Name:           jira
Version:        6.4.13
Release:        2%{?dist}
Summary:        Atlassian Jira with systemd integration

License:        Proprietary       
URL:            https://www.atlassian.com/software/jira
Source0:        https://www.atlassian.com/software/jira/downloads/binary/atlassian-%{name}-%{version}.tar.gz
Source1:        %{name}.service
Source2:        %{name}.sysconfig
Source3:        %{name}.tmpfilesd.conf
Patch0:         %{name}.00-increase-stop-timeout.patch

BuildRequires:  systemd
BuildRequires:  dos2unix

Requires:       %{name}-plain = %{version}
%{?systemd_requires}

%description
Atlassian Jira with systemd integration

%package plain
Summary:        Atlassian Jira
Requires:       shadow-utils

%description plain
Atlassian Jira without systemd integration

%prep
tar -xf %{SOURCE0}
cd atlassian-%{name}-%{version}-standalone

%patch0 -p1

# remove windows blobs
find ./ -name "*.bat" -delete
find ./ -name "*.exe" -delete
rm -rf ./bin/apr/

# unix line endings FTW!
dos2unix conf/*

install -d -m 755 integration
install -m 644 %{SOURCE1} integration/
install -m 644 %{SOURCE2} integration/
install -m 644 %{SOURCE3} integration/

sed -i 's|@JIRA_HOME@|%{jira_home}|g' integration/*
sed -i 's|@JIRA_INSTALL@|%{jira_install}|g' integration/*
sed -i 's|@JIRA_SYSTEMD_ENVFILE@|%{jira_systemd_envfile}|g' integration/*
sed -i 's|@JIRA_RUN@|%{jira_run}|g' integration/*

# JIRA application home directory
# https://confluence.atlassian.com/adminjiraserver073/jira-application-home-directory-861253888.html
sed -i 's|^jira\.home =.*|jira.home = %{jira_home}|' atlassian-jira/WEB-INF/classes/jira-application.properties

# Logging and profiling
# https://confluence.atlassian.com/adminjiraserver071/logging-and-profiling-802592962.html
sed -i 's|^log4j\.appender\.filelog=.*|log4j.appender.filelog=org.apache.log4j.RollingFileAppender|' atlassian-jira/WEB-INF/classes/log4j.properties
sed -i 's|^log4j\.appender\.filelog\.File=.*|log4j.appender.filelog.File=%{jira_log}/atlassian-jira.log|' atlassian-jira/WEB-INF/classes/log4j.properties


%build
cd atlassian-%{name}-%{version}-standalone

%install
rm -rf $RPM_BUILD_ROOT
cd atlassian-%{name}-%{version}-standalone

install -d -m 750 $RPM_BUILD_ROOT%{jira_conf}
install -d -m 750 $RPM_BUILD_ROOT%{jira_conf}/Catalina/localhost
install -d -m 750 $RPM_BUILD_ROOT%{jira_home}
install -d -m 750 $RPM_BUILD_ROOT%{jira_log}
install -d -m 755 $RPM_BUILD_ROOT%{jira_install}
install -d -m 755 $RPM_BUILD_ROOT%{jira_run}

install -m 640 conf/* $RPM_BUILD_ROOT%{jira_conf}
install -D -m 644 integration/%{name}.service $RPM_BUILD_ROOT%{_unitdir}/%{name}.service
install -D -m 644 integration/%{name}.tmpfilesd.conf $RPM_BUILD_ROOT%{_tmpfilesdir}/%{name}.conf
install -D -m 640 integration/%{name}.sysconfig $RPM_BUILD_ROOT%{jira_systemd_envfile}

ln --force --symbolic --relative $RPM_BUILD_ROOT%{jira_conf} $RPM_BUILD_ROOT%{jira_install}/conf 
ln --force --symbolic --relative $RPM_BUILD_ROOT%{jira_log} $RPM_BUILD_ROOT%{jira_install}/logs
ln --force --symbolic --relative $RPM_BUILD_ROOT%{jira_run} $RPM_BUILD_ROOT%{jira_install}/work
ln --force --symbolic --relative $RPM_BUILD_ROOT%{_tmppath} $RPM_BUILD_ROOT%{jira_install}/temp

cp -a atlassian-jira lib bin external-source \
  tomcat-docs webapps $RPM_BUILD_ROOT%{jira_install}

%pre plain
getent group jira >/dev/null || groupadd -r jira
getent passwd jira >/dev/null || \
    useradd -r -g jira -d %{jira_home} -s /sbin/nologin \
    -c "JIRA service user" jira

%post
%systemd_post %{name}.service

%preun
%systemd_preun %{name}.service

%postun
%systemd_postun_with_restart %{name}service

%files
%config(noreplace) %attr(640, root, root) %{jira_systemd_envfile}
%{_unitdir}/%{name}.service
%{_tmpfilesdir}/%{name}.conf

%files plain
%license atlassian-%{name}-%{version}-standalone/licenses/*
%doc atlassian-%{name}-%{version}-standalone/NOTICE
%doc atlassian-%{name}-%{version}-standalone/README*
%config(noreplace) %attr(-, root, jira) %{jira_conf}
%dir %{jira_install}

# Allow symlinked dirs to be replaced
%config(noreplace) %{jira_install}/conf
%config(noreplace) %{jira_install}/logs
%config(noreplace) %{jira_install}/temp
%config(noreplace) %{jira_install}/work

%{jira_install}/atlassian-jira
%{jira_install}/lib
%attr(755,root,root) %{jira_install}/bin
%{jira_install}/external-source
%{jira_install}/tomcat-docs
%{jira_install}/webapps
%dir %attr(750, jira, adm) %{jira_log}
%dir %attr(750, jira, jira) %{jira_home}
%dir %attr(750, jira, jira) %{jira_run}


%changelog
* Fri Mar  2 2018 Thomas Mueller <thomas@chaschperli.ch> - 7.8.0-1
- Initial release
