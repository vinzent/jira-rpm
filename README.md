# Atlassian Jira package for CentOS, RHEL & Fedora

The spec file creates these packages:

* jira-software-plain: the application
* jira-software: depends adds systemd service and SELinux integration
* jira-software-openjdk: as jira-software but depend on opendjk (only Oracle Java
  is supported by Atlassian)
* jira-software-selinux: selinux policy for jira

## What is where?

* */opt/atlassian/jira* - jira install directory
* */var/atlassian/application-data/jira* - the default `JIRA_HOME` directory
* */etc/opt/atlassian/jira* - the conf directory
* */var/log/atlassian/jira* - the log directory
* */etc/sysconfig/jira* - Env vars which systemd jira service will read
* */run/atlassian/jira* - the run directory (pid file)

## Quickstart


```
sudo yum install jira-software

# Add custom env (JAVA_HOME, JAVA_OPTS, JIRA_HOME, ...)
vi /etc/sysconfig/jira-software

sudo systemctl start jira-software

sudo systemctl status jira-software

xdg-open http://localhost:8080

sudo systemctl stop jira-software
```
