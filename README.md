# Atlassian Jira package for CentOS, RHEL & Fedora

The spec file creates 2 packages:

* jira-core: the application
* jira: depends on jira-core and adds systemd service integration


## What is where?

* */opt/atlassian/jira* - jira install directory
* */var/atlassian/application-data/jira* - the default `JIRA_HOME` directory
* */etc/opt/atlassian/jira* - the conf directory
* */var/log/atlassian/jira* - the log directory
* */etc/sysconfig/jira* - Env vars which systemd jira service will read
* */run/atlassian/jira* - the run directory (pid file)


## Quickstart


```
sudo yum install jira

sudo systemctl start jira

sudo systemctl status jira

xdg-open http://localhost:8080

sudo systemctl stop jira
```
