# Changelog

## Unreleased

## v0.5.0 (2025-02-22)
- Improved Python API authentication when using URL-based connectivity,
  by respecting the `credential` keyword argument
- Added basic example program about how to import a dashboard
- Options: Permitted usage without authentication credentials or token
- Options: Do not assume defaults for `ACTION` and `--grafana_label` args
- Options: Print help text when using erroneous parameters

## v0.4.0 (2024-10-16)
- Fixed folder argument issue
- Fixed import dashboards into a folder
- Added keep-uid argument to preserve the dashboard uid provided in file
- Added an option to import dashboards from a directory

Thanks, @vrymar.

## v0.3.0 (2024-10-03)
* Permit invocation without configuration file for ad hoc operations.
  In this mode, the Grafana URL can optionally be defined using the
  environment variable `GRAFANA_URL`.
* Fix exit codes in failure situations.
* Fix exception handling and propagation in failure situations.
* Add feature to support dashboard builders, in the spirit of
  dashboard-as-code. Supports Grafonnet, grafana-dashboard, grafanalib,
  and any other kind of executable program generating Grafana Dashboard
  JSON.
* Add watchdog feature, monitoring the input dashboard for changes on
  disk, and re-uploading it, when changed.
* Pass `GRAFANA_TOKEN` environment variable on Grafana initialization.
  Thanks, @jl2397.

## v0.2.0 (2022-02-05)
* Migrated from grafana_api to grafana_client
  
## v0.1.0 (2022-02-01)
* Fixed behavior for dashboard moved from one folder to another

## v0.0.3 (2022-02-31)
* Added "remove dashboard" feature

## v0.0.2 (2022-01-07)
* Changed config file format from json to yml
* Added labels in config to define multi grafana servers.

## v0.0.1 (2021-03-15)
* First release on GitHub.
