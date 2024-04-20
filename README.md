# Grafana import Tool

_Export and import Grafana dashboards using the [Grafana HTTP API] and
[grafana-client]._


## Features

- Export Grafana dashboards into JSON format.
- Import dashboards in JSON format into Grafana.
- Remove dashboards.


## Installation

```shell
pip install --upgrade 'git+https://github.com/peekjef72/grafana-import-tool.git'
```

Currently, there is no up-to-date version on PyPI, so we recommend to
install directly from the repository.


## Configuration

The configuration is stored in a YAML file. In order to connect to Grafana, you
will need an authentication token for Grafana.

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


## Usage

build a directory structure:
- grafana-import/
	- conf/grafana-import.yml
	where your main configuration file is
	- exports/
	where your exported dashboards will be stored.
	- imports/
	where your dashboards to import are stored.

Then, enter into your directory, and type in your commands.
Please note the import action preserves the version history.

`grafana-import --help`
```shell
usage: grafana-import [-h] [-a] [-b BASE_PATH] [-c CONFIG_FILE]
                      [-d DASHBOARD_NAME] [-g GRAFANA_LABEL]
                      [-f GRAFANA_FOLDER] [-i DASHBOARD_FILE] [-o] [-p] [-v]
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
  -g GRAFANA_LABEL, --grafana_label GRAFANA_LABEL
                        label in the config file that represents the grafana to
                        connect to.
  -f GRAFANA_FOLDER, --grafana_folder GRAFANA_FOLDER
                        the folder name where to import into Grafana.
  -i DASHBOARD_FILE, --dashboard_file DASHBOARD_FILE
                        path to the dashboard file to import into Grafana.
  -o, --overwrite       if a dashboard with same name exists in folder,
                        overwrite it with this new one.
  -p, --pretty          use JSON indentation when exporting or extraction of
                        dashboards.
  -v, --verbose         verbose mode; display log message to stdout.
  -V, --version         display program version and exit..

```


## Examples

### Import
Import a dashboard from a JSON file to the folder `Applications` in Grafana.
```shell
grafana-import  -i my-first-dashboard_202104011548.json -f Applications -o
```

### Export
Export the dashboard `my-first-dashboard` to the default export directory.
```bash
grafana-import -d "my-first-dashboard" -p export
```

### Delete
Delete the dashboard `my-first-dashboard` from folder `Applications`.
```bash
grafana-import -f Applications -d "my-first-dashboard" remove
```


[Grafana HTTP API]: https://grafana.com/docs/grafana/latest/http_api/
[grafana-client]: https://github.com/panodata/grafana-client
