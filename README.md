# Grafana import Tool

A python3 based application to play with grafana dashboards using [Grafana API](https://grafana.com/docs/grafana/latest/http_api/) and a python interface [grafana-client](https://github.com/panodata/grafana-client)

The aim of this tool is to:
1. Export easilly an existing Grafana dashboard from a folder.
2. Import a dashboard in JSON format into a Grafana.
3. Remove a dashboard

## Install using this repo

install github repository.

```bash
    $ pip install git+https://github.com/peekjef72/grafana-import-tool.git
```

## Requirements:

* bash
* python >3.6
* python modules:
  - jinja2
  - grafana_client 2.0.0 what will pull the dependencies
    - requests
    - idna
    - urllib3
    - certifi
    - chardet
* Access to a Grafana API server.
* A `Token` of an `Admin` role (grafana APIKey).

## Configuration
The configuration is stored in a YAML file.

It contains 2 parts:
* **general**: for script env.
	* **debug**: enable verbose (debug) trace (for dev only...)
	* **export_suffix**: when exporting a dashboard, append that suffix to the file name. The suffix can contain plain text and pattern that is translated with strftime command.
	* **export_path**: where to store the exported dashboards.
	* **import_path**: where to load the dashboards before to import then into grafana server.
- **grafana**: for grafana access settings; you can define several grafana acces with different api_key or grafana server url
  * **label**: a label to refer this grafana server default at least
    * **protocal**, **host**, **port**: use to build the access url
    * **verify_ssl**: to check ssl certificate or not
    * **token**: APIKEY with admin right from Grafana to access the REST API.
    * **search_api_limit**: the maximum element to retrieve on search over API.

<details>
example:

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
...
```

</details>

## Usages
build a directory structure:
- grafana-import/
	- conf/grafana-import.yml
	where your main configuration file is
	- exports/
	where your exported dashboards will be stored.
	- imports/
	where your dashboards to import are stored.

then enter into your directory and type in you commands.

**usage**: 
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
import action preserves the version history.

***Example:***
* **import** the dashboard located in default directory imports to grafana folder "Applications"

```bash
$ grafana-import  -i my-first-dashboard_202104011548.json -f Applications -o
OK: dashboard my-first-dashboard imported into 'Applications'.
```
then you can go into Grafana Gui and find the folder Applications

* **export** the dashboard 'my-first-dashboard' to default export directory:

```bash
$ /usr/local/bin/grafana-import -d "my-first-dashboard" -p export
OK: dashboard exported to './exports/my-first-dashboard_20210401165925.json'.
```
When the dashboard is not required anymore, you can remove it:
* **remove** the dashboard "my-first-dashboard" from folder "Applications"

```bash
$ grafana-import -f Applications -d "my-first-dashboard" remove
OK: dashboard my-first-dashboard removed from 'Applications'.
```


