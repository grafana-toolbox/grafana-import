# Grafana import Tool

A python3 bases application to play with grafana dashboards using [Grafana API](https://grafana.com/docs/grafana/latest/http_api/) and a python interface [grafana_api](https://github.com/m0nhawk/grafana_api)

The aim of this tool is to:
1. Export easilly an existing Grafana dashboard.
3. Import a dashboard in JSON format into a Grafana.

## Install using this repo

install with bitbuckt repo or github repo.

```bash
    $ pip install git+https://github.com/peekjef72/grafana-import-tool.git
```

## Requirements:

* bash
* python >3.6
* python modules:
  - jinja2
  - grafana-api 1.0.3 what will pull the dependencies
    - requests
    - idna
    - urllib3
    - certifi
    - chardet
* Access to a Grafana API server.
* A `Token` of an `Admin` role (grafana APIKey).
##WARNING##: 
 grafana-api package must be install from 'forked' repository (not official):

```bash
    $ pip install git+https://github.com/peekjef72/grafana_api.git
```
## Configuration
The configuration is stored in a JSON file, with extended syntax that authorize comments in C++ style with // or /*... */.
It contains 2 parts:
* **general**: for script env.
	* **debug**: enable verbose (debug) trace (for dev only...)
	* **export_suffix**: when exporting a dashboard, append that suffix to the file name. The suffix can contain plain text and pattern that is translated with strftime command.
	* **export_path**: where to store the exported dashboards.
	* **import_path**: where to load the dashboards before to import then into grafana server.
- **grafana**: for grafana access settings
	* **protocal**, **host**, **port**: use to build the access url
	* **verify_ssl**: to check ssl certificate or not
	* **token**: APIKEY with admin right from Grafana to access the REST API.
	* **search_api_limit**: the maximum element to retrieve on search over API.

## Usages
build a directory structure:
- grafana-import/
	- conf/grafana-import.json
	where your main configuration file is
	- exports/
	where your exported dashboards will be stored.
	- importds/
	where your dashboards to import are stored.

then enter into your directory and type in you commands.

**usage**: grafana-import [-h] [-b BASE_PATH] [-c CONFIG_FILE] [-d DASHBOARD_NAME]
                      [-f GRAFANA_FOLDER] [-i DASHBOARD_FILE] [-o] [-p] [-v]
                      [-V]
                      [ACTION]

import action preserves the version history.


***Example:***
* **import** the dashboard located in default directory imports to grafana folder "Application"

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



