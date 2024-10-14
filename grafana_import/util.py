import json
import logging
import os
import shlex
import subprocess
import sys
import typing as t
from pathlib import Path

import yaml

ConfigType = t.Dict[str, t.Any]
SettingsType = t.Dict[str, t.Union[str, int, bool]]


def setup_logging(level=logging.INFO, verbose: bool = False):
    log_format = "%(asctime)-15s [%(name)-26s] %(levelname)-8s: %(message)s"
    logging.basicConfig(format=log_format, stream=sys.stderr, level=level)


def load_yaml_config(config_file: str) -> ConfigType:
    """
    Load configuration file in YAML format from disk.
    """
    try:
        with open(config_file, "r") as cfg_fh:
            try:
                return yaml.safe_load(cfg_fh)
            except yaml.scanner.ScannerError as ex:
                mark = ex.problem_mark
                msg = "YAML file parsing failed : %s - line: %s column: %s => %s" % (
                    config_file,
                    mark and mark.line + 1,
                    mark and mark.column + 1,
                    ex.problem,
                )
                raise ValueError(f"Configuration file invalid: {config_file}. Reason: {msg}") from ex
    except Exception as ex:
        raise ValueError(f"Reading configuration file failed: {ex}") from ex


def grafana_settings(
    url: t.Union[str, None], config: t.Union[ConfigType, None], label: t.Union[str, None]
) -> SettingsType:
    """
    Acquire Grafana connection profile settings, and application settings.
    """

    params: SettingsType = {}

    # Grafana connectivity.
    if url or "GRAFANA_URL" in os.environ:
        params.update({"url": url or os.environ["GRAFANA_URL"]})
    if "GRAFANA_TOKEN" in os.environ:
        params.update({"token": os.environ["GRAFANA_TOKEN"]})

    if not params and config is not None and label is not None:
        params = grafana_settings_from_config_section(config=config, label=label)

    # Additional application parameters.
    if config is not None:
        params.update(
            {
                "search_api_limit": config.get("grafana", {}).get("search_api_limit", 5000),
                "folder": config.get("general", {}).get("grafana_folder", "General"),
            }
        )
    return params


def grafana_settings_from_config_section(config: ConfigType, label: t.Union[str, None]) -> SettingsType:
    """
    Extract Grafana connection profile from configuration dictionary, by label.

    The configuration contains multiple connection profiles within the `grafana`
    section. In order to address a specific profile, this function accepts a
    `label` string.
    """
    if not label or not config.get("grafana", {}).get(label):
        raise ValueError(f"Invalid Grafana configuration label: {label}")

    # Initialize default configuration from Grafana by label.
    # FIXME: That is certainly a code smell.
    #        Q: Has it been introduced later in order to support multiple connection profiles?
    #        Q: Is it needed to update the original `config` dict, or can it just be omitted?
    config["grafana"] = config["grafana"][label]

    if "token" not in config["grafana"]:
        raise ValueError(f"Authentication token missing in Grafana configuration at: {label}")

    return {
        "host": config["grafana"].get("host", "localhost"),
        "protocol": config["grafana"].get("protocol", "http"),
        "port": config["grafana"].get("port", "3000"),
        "token": config["grafana"].get("token"),
        "verify_ssl": config["grafana"].get("verify_ssl", True),
    }


def file_is_executable(path: t.Union[str, Path]) -> bool:
    """
    Is this file executable?

    https://bugs.python.org/issue42497
    """
    return os.access(str(path), os.X_OK)


def read_dashboard_file(path: t.Union[str, Path]) -> t.Dict[str, t.Any]:
    """
    Read dashboard file, and return its representation.
    """

    path = Path(path)

    if path.suffix == ".json":
        try:
            with open(path, "r") as f:
                payload = f.read()
        except OSError as ex:
            raise IOError(f"Reading file failed: {path}. Reason: {ex.strerror}") from ex

    elif path.suffix == ".jsonnet":
        # jsonnet --jpath vendor faro.jsonnet
        command = f"jsonnet --jpath {path.parent / 'vendor'} {path}"
        payload = subprocess.check_output(shlex.split(command), encoding="utf-8")  # noqa: S603

    elif path.suffix == ".py":
        command = f"{sys.executable} {path}"
        payload = subprocess.check_output(shlex.split(command), encoding="utf-8")  # noqa: S603

    elif file_is_executable(path):
        payload = subprocess.check_output([path], shell=True, encoding="utf-8")  # noqa: S602, S603

    else:
        raise NotImplementedError(f"Decoding file type not implemented, or file is not executable: {path.name}")

    try:
        return json.loads(payload)
    except json.JSONDecodeError as ex:
        raise IOError(f"Decoding JSON output from file failed: {path}. Reason: {ex}") from ex
