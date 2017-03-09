# How-to use the automated setup.json

## Description

This repository contains the automation library for Open vStorage.
This library delegates component creation/removal to the REST API of Open vStorage through Python code.

## System requirements

- python-timeout-decorator
- python 2.7
- python 3
- Open vStorage (must be ran on ovs node)

## Prerequisites

- Open vStorage main directory: `/opt/OpenvStorage`
- Automation library main directory: `/opt/OpenvStorage/ci`
- Automation library main config directory `/opt/OpenvStorage/ci/config`
- Automation library settings file `/opt/OpenvStorage/ci/config/settings.json`
- Automation library logging directory `/var/log/ovs`
- Automation library SETUP logging file `/var/log/ovs/setup.log`
- Automation library VALIDATION logging file `/var/log/ovs/validation.log`
- Automation library REMOVE logging file `/var/log/ovs/remove.log`
- Automation library DECORATORS logging file `/var/log/ovs/decorators.log`
- Automation library HELPERS logging file `/var/log/ovs/helpers.log`

### Scenarios section
Contains the information what test need to be executed if `ci/scenarios` is enabled.

