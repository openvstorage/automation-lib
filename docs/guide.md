# How-to use the automated library

## Description

This repository contains the automation library for Open vStorage.

## System requirements

- python-timeout-decorator
- python 2.7
- python 3
- Open vStorage (must be ran on ovs node)

## Prerequisites

- Open vStorage main directory: `/opt/OpenvStorage`
- Open vStorage logging directory `/var/log/ovs`
- Automation library main directory: `/opt/OpenvStorage/ci`
- Automation library main config directory `/opt/OpenvStorage/ci/config`
- Automation library settings file `/opt/OpenvStorage/ci/config/settings.json`
- Automation library SETUP logging file `/var/log/ovs/setup.log`
- Automation library VALIDATION logging file `/var/log/ovs/validation.log`
- Automation library REMOVE logging file `/var/log/ovs/remove.log`
- Automation library DECORATORS logging file `/var/log/ovs/decorators.log`
- Automation library HELPERS logging file `/var/log/ovs/helpers.log`

## Sections
### Api Library
This library delegates component creation/removal to the REST API of Open vStorage through Python code.

#### Helpers section
Contains functions to assist in removal, setup and validation of components such as backends, disks, storagerouters and -drivers, as well as gathering of metadata etc.

#### Remove section
Contains functions for removal of arakoon clusters, backends, roles, vDisks and vPools from Open vStorage.

#### Setup section
Contains functions to set up new arakoon clusters, backends, domains, proxies, roles, vDisks and vPools in Open vStorage.

#### Validation section
Contains function to validate functionality of Open vStorage components. 
This includes decorators for checking prerequisites of functions throughout the package.

###Scenario helpers section
Classes in this section are used to execute the actual tests (referred to as[scenarios](#header_scenarios))

###<a name="header_scenarios"></a>Scenarios section
This section contains code for testing a variety of integration scenarios.\
Currently present tests:
- api checkup post-reboot
- several arakoon related checks
- addition and removal of
    - backends
    - storagerouters
    - vDisks, vMachines and vPools
- health checks
- installation tests
- hypervisor tests


