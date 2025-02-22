# Grafana import Tool

[![Tests](https://github.com/grafana-toolbox/grafana-import/actions/workflows/tests.yml/badge.svg)](https://github.com/grafana-toolbox/grafana-import/actions/workflows/tests.yml)
[![Coverage](https://codecov.io/gh/grafana-toolbox/grafana-import/branch/main/graph/badge.svg)](https://app.codecov.io/gh/grafana-toolbox/grafana-import)
[![PyPI Version](https://img.shields.io/pypi/v/grafana-import.svg)](https://pypi.org/project/grafana-import/)
[![Python Version](https://img.shields.io/pypi/pyversions/grafana-import.svg)](https://pypi.org/project/grafana-import/)
[![PyPI Downloads](https://pepy.tech/badge/grafana-import/month)](https://pepy.tech/project/grafana-import/)
[![Status](https://img.shields.io/pypi/status/grafana-import.svg)](https://pypi.org/project/grafana-import/)
[![License](https://img.shields.io/pypi/l/grafana-import.svg)](https://pypi.org/project/grafana-import/)

_Export and import Grafana dashboards using the [Grafana HTTP API] and
[grafana-client]._


## Features

- Export dashboards into JSON format.
- Import dashboards into Grafana, both in native JSON format, or
  emitted by dashboard builders, supporting dashboard-as-code workflows.
  - Supported builders are [Grafonnet], [grafana-dashboard], [grafanalib],
    and any other executable program which emits Grafana Dashboard JSON
    on STDOUT.
  - The import action preserves the version history of dashboards.
- Watchdog: For a maximum of authoring and editing efficiency, the
  watchdog monitors the input dashboard for changes on disk, and
  re-uploads it to the Grafana API, when changed.
- Remove dashboards.


## Installation

```shell
pip install --upgrade 'grafana-import[builder]'
```

The command outlined above describes a full installation of `grafana-import`,
including support for dashboard builders, aka. dashboard-as-code.

## Synopsis

### Command-line use
```shell
grafana-import import -u http://admin:admin@localhost:3000 -i grafana_dashboard.json --overwrite
```

### API use
```python
import json
from pathlib import Path
from grafana_import.grafana import Grafana

dashboard = json.loads(Path("grafana_dashboard.json").read_text())
gio = Grafana(url="http://localhost:3000", credential=("admin", "admin"))
outcome = gio.import_dashboard(dashboard)
```

## Ad Hoc Usage

You can use `grafana-import` in ad hoc mode without a configuration file.

### Getting started

In order to do some orientation flights, start a Grafana instance using Podman
or Docker.
```shell
docker run --rm -it --name=grafana --publish=3000:3000 \
  --env='GF_SECURITY_ADMIN_PASSWORD=admin' grafana/grafana:latest
```

If you don't have any Grafana dashboard representations at hand, you can
acquire some from the `examples` directory within the `grafana-import`
repository, like this.
```shell
wget https://github.com/grafana-toolbox/grafana-snippets/raw/main/dashboard/native-play-influxdb.json
wget https://github.com/grafana-toolbox/grafana-snippets/raw/main/dashboard/gd-prometheus.py
```

Define Grafana endpoint.
```shell
export GRAFANA_URL=http://admin:admin@localhost:3000
```

### Import from JSON
Import a dashboard from a JSON file.
```shell
grafana-import import -i native-play-influxdb.json
```

### Import using a builder
Import a dashboard emitted by a dashboard builder, overwriting it
when a dashboard with the same name already exists in the same folder.
```shell
grafana-import import --overwrite -i gd-prometheus.py
```

### Import using reloading
Watch the input dashboard for changes on disk, and re-upload it, when changed.
```shell
grafana-import import --overwrite --reload -i gd-prometheus.py
```

### Import dashboards from a directory
Import all dashboards from provided directory
```shell
grafana-import import -i "./dashboards_folder"
```

### Export
Export the dashboard titled `my-first-dashboard` to the default export directory.
```bash
grafana-import export --pretty -d "my-first-dashboard"
```

### Delete
Delete the dashboard titled `my-first-dashboard` from folder `Applications`.
```bash
grafana-import remove -f Applications -d "my-first-dashboard"
```


## Usage with Configuration File

You can also use `grafana-import` with a configuration file. In this way, you
can manage and use different Grafana connection profiles, and also use presets
for application-wide configuration settings.

The configuration is stored in a YAML file. In order to use it optimally,
build a directory structure like this:
```
grafana-import/
- conf/grafana-import.yml
  Path to your main configuration file.
- exports/
  Path where exported dashboards will be stored.
- imports/
  Path where dashboards are imported from.
```

Then, enter into your directory, and type in your commands.

The configuration file uses two sections, `general`, and `grafana`.

### `general` section
Configure program directories.

* **debug**: enable verbose (debug) trace (for dev only...)
* **export_suffix**: when exporting a dashboard, append that suffix to the file name. The suffix can contain plain text and pattern that is translated with strftime command.
* **export_path**: where to store the exported dashboards.
* **import_path**: where to load the dashboards before to import then into grafana server.

### `grafana` section

Grafana authentication settings. You can define multiple Grafana access
configuration sections using different settings for `api_key` or Grafana
server URL.

* **label**: A label to refer this Grafana server, e.g. `default`
  * **protocol**, **host**, **port**: use to build the access url
  * **verify_ssl**: to check ssl certificate or not
  * **token**: APIKEY with admin right from Grafana to access the REST API.
  * **search_api_limit**: the maximum element to retrieve on search over API.

<details>

**Example:**

```yaml
---

  general:
    debug: false
    import_folder: test_import

  grafana:
    default:
      protocol: http
      host: localhost
      port: 3000
      token: "____APIKEY____"
      search_api_limit: 5000
      verify_ssl: true
```
</details>


## Authentication

In order to connect to Grafana, you can use either vanilla credentials
(username/password), or an authentication token. Because `grafana-import`
uses `grafana-client`, the same features for defining authentication
settings can be used. See also [grafana-client authentication variants].

Vanilla credentials can be embedded into the Grafana URL, to be supplied
using the `--grafana_url` command line argument, or the `GRAFANA_URL`
environment variable. For specifying a Grafana authentication token without
using a configuration file, use the `GRAFANA_TOKEN` environment variable.

[grafana-client authentication variants]: https://github.com/panodata/grafana-client/#authentication


## Builders

grafana-import provides support for dashboard-as-code builders.

To get inspired what you can do, by reading more examples, please also visit
[grafonnet examples], [grafana-dashboard examples], and [grafanalib examples].

### Grafonnet

[Grafonnet] is a [Jsonnet] library for generating Grafana dashboards.

The library is generated from JSON Schemas generated by Grok. In turn,
these schemas are generated directly from the Grafana repository, in
order to ensure Grafonnet is always synchronized with the development
of Grafana without much friction.

#### Install
Install Jsonnet, and its jsonnet-bundler package manager.
```shell
brew install go-jsonnet jsonnet-bundler
```
Install Grafonnet into a Jsonnet project.
```shell
git clone https://github.com/grafana-toolbox/grafana-snippets
cd grafana-snippets/dashboard/grafonnet-simple
jb install github.com/grafana/grafonnet/gen/grafonnet-latest@main
```

#### Usage
Render dashboard defined in [Grafonnet]/[Jsonnet].
```shell
grafana-import import --overwrite -i ./path/to/faro.jsonnet
```

### grafana-dashboard
Render dashboard defined using [grafana-dashboard].
```shell
grafana-import import --overwrite -i ./path/to/gd-dashboard.py
```

### grafanalib
Render dashboard defined using [grafanalib].
```shell
grafana-import import --overwrite -i ./path/to/gl-dashboard.py
```


## Help

`grafana-import --help`
```shell
usage: grafana-import [-h] [-a] [-b BASE_PATH] [-c CONFIG_FILE]
                      [-d DASHBOARD_NAME] [-g GRAFANA_LABEL]
                      [-f GRAFANA_FOLDER] [-i DASHBOARD_FILE] [-o] [-p] [-v] [-k]
                      [-V]
                      [ACTION]

play with grafana dashboards json files.

positional arguments:
  ACTION                action to perform. Is one of 'export', 'import'
                        (default), or 'remove'.
                        export: lookup for dashboard name in Grafana and dump
                          it to local file.
                        import: import a local dashboard file (previously 
                          exported) to Grafana.
                        remove: lookup for dashboard name in Grafana and remove
                          it from Grafana server.


optional arguments:
  -h, --help            show this help message and exit
  -a, --allow_new       if a dashboard with same name exists in an another
                        folder, allow to create a new dashboard with same name
                        it that folder.
  -b BASE_PATH, --base_path BASE_PATH
                        set base directory to find default files.
  -c CONFIG_FILE, --config_file CONFIG_FILE
                        path to config files.
  -d DASHBOARD_NAME, --dashboard_name DASHBOARD_NAME
                        name of dashboard to export.
  -u GRAFANA_URL, --grafana_url GRAFANA_URL
                        Grafana URL to connect to.
  -g GRAFANA_LABEL, --grafana_label GRAFANA_LABEL
                        label in the config file that represents the grafana to
                        connect to.
  -f GRAFANA_FOLDER, --grafana_folder GRAFANA_FOLDER
                        the folder name where to import into Grafana.
  -i DASHBOARD_FILE, --dashboard_file DASHBOARD_FILE
                        path to the dashboard file to import into Grafana.
  -k  --keep_uid        keep uid defined in dashboard file to import into Grafana. When dashboard is overriden, the uid is also overriden.
  -o, --overwrite       if a dashboard with same name exists in folder,
                        overwrite it with this new one.
  -r, --reload          Watch the input dashboard for changes on disk, and
                        re-upload it, when changed.
  -p, --pretty          use JSON indentation when exporting or extraction of
                        dashboards.
  -v, --verbose         verbose mode; display log message to stdout.
  -V, --version         display program version and exit.

```

## Prior Art

- https://grafana.com/blog/2020/02/26/how-to-configure-grafana-as-code/
- https://grafana.com/blog/2022/12/06/a-complete-guide-to-managing-grafana-as-code-tools-tips-and-tricks/
- https://grafana.github.io/grizzly/
  https://grafana.github.io/grizzly/what-is-grizzly/
- https://docs.ansible.com/ansible/latest/collections/grafana/grafana/dashboard_module.html#ansible-collections-grafana-grafana-dashboard-module
- https://blog.kevingomez.fr/2023/03/07/three-years-of-grafana-dashboards-as-code/
- https://github.com/K-Phoen/grabana
- https://github.com/K-Phoen/dark
- https://github.com/grafana/scenes


## Contributing

Contributions are welcome, and they are greatly appreciated. You can contribute
in many ways, and credit will always be given.

For learning more how to contribute, see the [contribution guidelines] and
learn how to set up a [development sandbox].


[contribution guidelines]: ./CONTRIBUTING.md
[development sandbox]: ./docs/sandbox.md
[Grafana HTTP API]: https://grafana.com/docs/grafana/latest/http_api/
[grafana-client]: https://github.com/panodata/grafana-client
[grafana-dashboard]: https://github.com/fzyzcjy/grafana_dashboard_python
[grafana-dashboard examples]: https://github.com/fzyzcjy/grafana_dashboard_python/tree/master/examples
[grafanalib]: https://github.com/weaveworks/grafanalib
[grafanalib examples]: https://github.com/weaveworks/grafanalib/tree/main/grafanalib/tests/examples
[Grafonnet]: https://github.com/grafana/grafonnet
[grafonnet examples]: https://github.com/grafana/grafonnet/tree/main/examples
[Jsonnet]: https://github.com/google/go-jsonnet
