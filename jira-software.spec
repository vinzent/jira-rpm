%define debug_package %{nil}
%define __jar_repack %{nil}
%global __provides_exclude ^osgi.*$
%global __requires_exclude ^osgi.*$
%global selinux_variants mls targeted

%global jira_install /opt/atlassian/jira
%global jira_conf %{_sysconfdir}%{jira_install}
%global jira_home %{_localstatedir}/atlassian/application-data/jira
%global jira_log %{_localstatedir}/log/atlassian/jira
%global jira_run %{_rundir}/atlassian/jira

%global jira_systemd_envfile %{_sysconfdir}/sysconfig/%{name}

Name:           jira-software
Version:        7.8.0
Release:        1.4.0%{?dist}
Summary:        Atlassian Jira with systemd integration

License:        Proprietary       
URL:            https://www.atlassian.com/software/jira
Source0:        https://www.atlassian.com/software/jira/downloads/binary/atlassian-%{name}-%{version}.tar.gz
Source1:        jira-software.service
Source2:        jira-software.sysconfig
Source3:        jira-software.tmpfilesd.conf
Source4:        jira.te
Source5:        jira.fc
Patch0:         jira-software.00-increase-stop-timeout.patch
Patch1:         jira-software.01-loosen-java-check.patch

BuildRequires:  systemd
BuildRequires:  dos2unix
BuildRequires:  checkpolicy, selinux-policy-devel

Requires:       %{name}-plain = %{version}
Requires:       %{name}-selinux = %{version}
%{?systemd_requires}

%description
Atlassian Jira with systemd integration

%package plain
Summary:        Atlassian Jira
Requires:       shadow-utils

%description plain
Atlassian Jira without systemd integration

%package openjdk
Summary:        Atlassian Jira with OpenJDK dependency
Requires:       java-1.8.0-headless
Requires:       %{name} = %{version}

%description openjdk
Atlassian Jira with OpenJDK dependency (unsupported by Atlassian)

%package selinux
Summary:        Atlassian Jira SELinux policy
%if "%{_selinux_policy_version}" != ""
Requires:       selinux-policy >= %{_selinux_policy_version}
%endif
Requires: /usr/sbin/semodule, /sbin/restorecon, /sbin/fixfiles

%description selinux
Atlassian Jira SELinux policy

%prep
tar -xf %{SOURCE0}
cd atlassian-%{name}-%{version}-standalone

%patch0 -p1
%patch1 -p1

# remove windows blobs
find ./ -name "*.bat" -delete
find ./ -name "*.exe" -delete
find ./ -name "*.exe.x64" -delete
rm -rf ./bin/apr/

# unix line endings FTW!
dos2unix conf/*

# JIRA application home directory
# https://confluence.atlassian.com/adminjiraserver073/jira-application-home-directory-861253888.html
sed -i 's|^jira\.home =.*|jira.home = %{jira_home}|' atlassian-jira/WEB-INF/classes/jira-application.properties

install -d -m 755 integration
install -m 644 %{SOURCE1} integration/
install -m 644 %{SOURCE2} integration/
install -m 644 %{SOURCE3} integration/

sed -i 's|@JIRA_HOME@|%{jira_home}|g' integration/*
sed -i 's|@JIRA_INSTALL@|%{jira_install}|g' integration/*
sed -i 's|@JIRA_SYSTEMD_ENVFILE@|%{jira_systemd_envfile}|g' integration/*
sed -i 's|@JIRA_RUN@|%{jira_run}|g' integration/*

install -d -m 755 SELinux
install -m 644 %{SOURCE4} %{SOURCE5} SELinux/


%build
cd atlassian-%{name}-%{version}-standalone

cd SELinux
for selinuxvariant in %{selinux_variants}
do
  make NAME=${selinuxvariant} -f /usr/share/selinux/devel/Makefile
  mv jira.pp jira.pp.${selinuxvariant}
  make NAME=${selinuxvariant} -f /usr/share/selinux/devel/Makefile clean
done
cd -

%install
rm -rf $RPM_BUILD_ROOT
cd atlassian-%{name}-%{version}-standalone

install -d -m 750 $RPM_BUILD_ROOT%{jira_conf}
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

for selinuxvariant in %{selinux_variants}
do
  install -d %{buildroot}%{_datadir}/selinux/${selinuxvariant}
  install -p -m 644 SELinux/jira.pp.${selinuxvariant} \
    %{buildroot}%{_datadir}/selinux/${selinuxvariant}/jira.pp
done

%pre plain
getent group jira >/dev/null || groupadd -r jira
getent passwd jira >/dev/null || \
    useradd -r -g jira -d %{jira_home} -s /sbin/nologin \
    -c "JIRA service user" jira

%post
%systemd_post %{name}.service

%post selinux
for selinuxvariant in %{selinux_variants}
do
  /usr/sbin/semodule -s ${selinuxvariant} -i \
    %{_datadir}/selinux/${selinuxvariant}/jira.pp &> /dev/null || :
done
/sbin/fixfiles -R %{name},%{name}-plain restore || :
/sbin/restorecon -Ri %{jira_home} %{jira_conf} %{jira_log} %{jira_install} %{jira_run} || :


%preun
%systemd_preun %{name}.service

%postun
%systemd_postun_with_restart %{name}service

%postun selinux
if [ $1 -eq 0 ] ; then
  for selinuxvariant in %{selinux_variants}
  do
    /usr/sbin/semodule -s ${selinuxvariant} -r jira &> /dev/null || :
  done
  /sbin/fixfiles -R %{name},%{name}-plain restore || :
  /sbin/restorecon -Ri %{jira_home} %{jira_conf} %{jira_log} %{jira_install} %{jira_run} || :
fi

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
# some of them are config files.
# https://confluence.atlassian.com/adminjiraserver/important-directories-and-files-938847744.html
%config(noreplace) %{jira_install}/atlassian-jira/WEB-INF/classes/jira-application.properties
%config(noreplace) %{jira_install}/atlassian-jira/WEB-INF/classes/log4j.properties
%config(noreplace) %{jira_install}/atlassian-jira/WEB-INF/classes/entityengine.xml
%config(noreplace) %{jira_install}/atlassian-jira/WEB-INF/classes/seraph-config.xml

%{jira_install}/lib
%attr(755,root,root) %{jira_install}/bin
%{jira_install}/external-source
%{jira_install}/tomcat-docs
%{jira_install}/webapps
%dir %attr(750, jira, adm) %{jira_log}
%dir %attr(750, jira, jira) %{jira_home}
%dir %attr(750, jira, jira) %{jira_run}

%files openjdk

%files selinux
%defattr(-,root,root,0755)
%doc atlassian-%{name}-%{version}-standalone/SELinux/*
%{_datadir}/selinux/*/jira.pp


%changelog
* Fri Mar  2 2018 Thomas Mueller <thomas@chaschperli.ch> - 7.8.0-1
- Initial release
