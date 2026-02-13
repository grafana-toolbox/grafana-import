"""
Created on Mon March 15th 2021

@author: jfpik

Suivi des modifications :
    V 0.0.0 - 2021/03/15 - JF. PIK - initial version

"""

import argparse
import json
import logging
import os
import re
import sys
import traceback
from datetime import datetime

import grafana_client.client as GrafanaApi

import grafana_import.grafana as Grafana
from grafana_import.constants import CONFIG_NAME, PKG_NAME, PKG_VERSION
from grafana_import.service import watchdog_service
from grafana_import.util import (
    grafana_settings,
    load_yaml_config,
    read_dashboard_file,
    setup_logging,
)

config = None


def save_dashboard(config, args, base_path, dashboard_name, dashboard, action):

    output_file = base_path
    file_name = dashboard_name

    if "exports_path" in config["general"] and not re.search(
        r"^(\.|\/)?/", config["general"]["exports_path"]
    ):
        output_file = os.path.join(output_file, config["general"]["exports_path"])

    if "export_suffix" in config["general"]:
        file_name += datetime.today().strftime(config["general"]["export_suffix"])

    if (
        "meta" in dashboard
        and "folderId" in dashboard["meta"]
        and dashboard["meta"]["folderId"] != 0
    ):
        file_name = dashboard["meta"]["folderTitle"] + "_" + file_name

    file_name = Grafana.remove_accents_and_space(file_name)
    output_file = os.path.join(output_file, file_name + ".json")

    # Create directory structure if it doesn't exist
    output_dir = os.path.dirname(output_file)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    try:
        output = open(output_file, "w")
    except OSError as e:
        logger.error("File {0} error: {1}.".format(output_file, e.strerror))
        sys.exit(2)

    content = None
    if args.pretty:
        content = json.dumps(dashboard["dashboard"], sort_keys=True, indent=2)
    else:
        content = json.dumps(dashboard["dashboard"])
    output.write(content)
    output.close()
    logger.info(f"OK: Dashboard '{dashboard_name}' {action} to: {output_file}")


class myArgs:
    attrs = [
        "pattern",
        "base_path",
        "config_file",
        "grafana",
        "dashboard_name",
        "pretty",
        "overwrite",
        "allow_new",
        "verbose",
        "keep_uid",
    ]

    def __init__(self):

        for attr in myArgs.attrs:
            setattr(self, attr, None)

    def __repr__(self):
        obj = {}
        for attr in myArgs.attrs:
            val = getattr(self, attr)
            if val is not None:
                obj[attr] = val
        return json.dumps(obj)


logger = logging.getLogger(__name__)


def main():

    setup_logging()

    # Get command line arguments.
    parser = argparse.ArgumentParser(
        description="play with grafana dashboards json files."
    )

    def print_help_and_exit():
        parser.print_help(sys.stderr)
        parser.exit(1)

    parser.add_argument(
        "-a",
        "--allow_new",
        action="store_true",
        default=False,
        help="If a dashboard with same name exists in an another folder, "
        "allow to create a new dashboard with same name it that folder.",
    )

    parser.add_argument(
        "-b", "--base_path", help="set base directory to find default files."
    )
    parser.add_argument("-c", "--config_file", help="path to config files.")

    parser.add_argument("-d", "--dashboard_name", help="name of dashboard to export.")

    parser.add_argument(
        "-u", "--grafana_url", help="Grafana URL to connect to.", required=False
    )

    parser.add_argument(
        "-g",
        "--grafana_label",
        help="label in the config file that represents the grafana to connect to.",
    )

    parser.add_argument(
        "-f", "--grafana_folder", help="the folder name where to import into Grafana."
    )

    parser.add_argument(
        "-i",
        "--dashboard_file",
        help="path to the dashboard file to import into Grafana.",
    )

    parser.add_argument(
        "-o",
        "--overwrite",
        action="store_true",
        default=False,
        help="if a dashboard with same name exists in same folder, overwrite it with this new one.",
    )

    parser.add_argument(
        "-r",
        "--reload",
        action="store_true",
        default=False,
        help="Watch the input dashboard for changes on disk, and re-upload it, when changed.",
    )

    parser.add_argument(
        "-p",
        "--pretty",
        action="store_true",
        help="use JSON indentation when exporting or extraction of dashboards.",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="verbose mode; display log message to stdout.",
    )

    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version="{0} {1}".format(PKG_NAME, PKG_VERSION),
        help="display program version and exit..",
    )

    parser.add_argument(
        "action",
        metavar="ACTION",
        nargs="?",
        choices=["import", "export", "remove"],
        help="action to perform. Is one of 'export', 'import' (default), or 'remove'.\n"
        "export: lookup for dashboard name in Grafana and dump it to local file.\n"
        "import: import a local dashboard file (previously exported) to Grafana.\n"
        "remove: lookup for dashboard name in Grafana and remove it from Grafana server.",
    )

    parser.add_argument(
        "-k",
        "--keep_uid",
        action="store_true",
        default=False,
        help="when importing dashboard, keep dashboard uid defined in the json file.",
    )

    inArgs = myArgs()
    args = parser.parse_args(namespace=inArgs)

    base_path = os.curdir
    if args.base_path is not None:
        base_path = inArgs.base_path

    if args.config_file is None:
        config = {"general": {"debug": False}}
    else:
        config_file = os.path.join(base_path, CONFIG_NAME)
        if not re.search(r"^(\.|\/)?/", config_file):
            config_file = os.path.join(base_path, args.config_file)
        else:
            config_file = args.config_file
        config = load_yaml_config(config_file)

    if args.verbose is None:
        if "debug" in config["general"]:
            args.verbose = config["general"]["debug"]
        else:
            args.verbose = False

    if args.allow_new is None:
        args.allow_new = False

    if args.overwrite is None:
        args.overwrite = False

    if args.pretty is None:
        args.pretty = False

    if args.dashboard_name is not None:
        config["general"]["dashboard_name"] = args.dashboard_name

    if args.action == "exporter" and (
        "dashboard_name" not in config["general"]
        or config["general"]["dashboard_name"] is None
    ):
        logger.error("ERROR: no dashboard has been specified.")
        sys.exit(1)

    config["check_folder"] = False
    if args.grafana_folder is not None:
        config["general"]["grafana_folder"] = args.grafana_folder
        config["check_folder"] = True

    if (
        "export_suffix" not in config["general"]
        or config["general"]["export_suffix"] is None
    ):
        config["general"]["export_suffix"] = "_%Y%m%d%H%M%S"

    if args.keep_uid is None:
        args.keep_uid = False

    params = grafana_settings(
        url=args.grafana_url, config=config, label=args.grafana_label
    )
    params.update(
        {
            "overwrite": args.overwrite,
            "allow_new": args.allow_new,
            "keep_uid": args.keep_uid,
        }
    )

    try:
        grafana_api = Grafana.Grafana(**params)
    except Exception as ex:
        logger.error(str(ex))
        sys.exit(1)

    # Import
    if args.action == "import":
        if args.dashboard_file is None:
            logger.error("ERROR: no file to import provided!")
            sys.exit(1)

        # Compute effective input file path.
        import_path = ""
        import_file = args.dashboard_file
        import_files = []

        if not re.search(r"^(?:(?:/)|(?:\.?\./))", import_file):
            import_path = base_path
            if "import_path" in config["general"]:
                import_path = os.path.join(import_path, config["general"]["import_path"])
            import_file = os.path.join(import_path, import_file)
            import_files.append(import_file)
        else:
            if os.path.isfile(import_file):
                logger.info(f"The path is a file: '{import_file}'")
                import_file = os.path.join(import_path, import_file)
                import_files.append(import_file)

            if os.path.isdir(import_file):
                logger.info(f"The path is a directory: '{import_file}'")
                import_files = [
                    os.path.join(import_file, f)
                    for f in os.listdir(import_file)
                    if os.path.isfile(os.path.join(import_file, f))
                ]
                logger.info(
                    f"Found the following files: '{import_files}' in dir '{import_file}'"
                )

        def process_dashboard(file_path):
            try:
                dash = read_dashboard_file(file_path)
            except Exception as ex:
                msg = f"Failed to load dashboard from: {file_path}. Reason: {ex}"
                logger.exception(msg)
                raise IOError(msg) from ex

            try:
                res = grafana_api.import_dashboard(dash)
            except GrafanaApi.GrafanaClientError as ex:
                msg = f"Failed to upload dashboard to Grafana. Reason: {ex}"
                logger.exception(msg)
                raise IOError(msg) from ex

            title = dash["title"]
            folder_name = grafana_api.grafana_folder
            if res:
                logger.info(f"Dashboard '{title}' imported into folder '{folder_name}'")
            else:
                msg = f"Failed to import dashboard into Grafana. title={title}, folder={folder_name}"
                logger.error(msg)
                raise IOError(msg)

        for file in import_files:
            print(f"Processing file: {file}")
            try:
                process_dashboard(file)
            except Exception as e:
                logger.error(f"Failed to process file {file}. Reason: {str(e)}")
                continue

        if args.reload:
            for file in import_files:
                watchdog_service(import_file, process_dashboard(file))

        sys.exit(0)

    # Remove
    elif args.action == "remove":
        dashboard_name = config["general"]["dashboard_name"]
        try:
            grafana_api.remove_dashboard(dashboard_name)
            logger.info(f"OK: Dashboard removed: {dashboard_name}")
            sys.exit(0)
        except Grafana.GrafanaDashboardNotFoundError as exp:
            logger.info(
                f"KO: Dashboard not found in folder '{exp.folder}': {exp.dashboard}"
            )
            sys.exit(1)
        except Grafana.GrafanaFolderNotFoundError as exp:
            logger.info(f"KO: Folder not found: {exp.folder}")
            sys.exit(1)
        except GrafanaApi.GrafanaBadInputError as exp:
            logger.info(f"KO: Removing dashboard failed: {dashboard_name}. Reason: {exp}")
            sys.exit(1)
        except Exception:
            logger.info(
                "ERROR: Dashboard '{0}' remove exception '{1}'".format(
                    dashboard_name, traceback.format_exc()
                )
            )
            sys.exit(1)

    # Export
    elif args.action == "export":
        dashboard_name = config["general"]["dashboard_name"]
        try:
            dash = grafana_api.export_dashboard(dashboard_name)
        except (
            Grafana.GrafanaFolderNotFoundError,
            Grafana.GrafanaDashboardNotFoundError,
        ):
            logger.info("KO: Dashboard name not found: {0}".format(dashboard_name))
            sys.exit(1)
        except Exception:
            logger.info(
                "ERROR: Dashboard '{0}' export exception '{1}'".format(
                    dashboard_name, traceback.format_exc()
                )
            )
            sys.exit(1)

        if dash is not None:
            save_dashboard(config, args, base_path, dashboard_name, dash, "exported")
            sys.exit(0)

    else:
        logger.error(
            f"Unknown action: {args.action}. Use one of: {parser._actions[-2].choices}"
        )
        print_help_and_exit()


if __name__ == "__main__":
    main()
