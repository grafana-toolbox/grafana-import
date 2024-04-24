from pathlib import Path

import pytest
import requests

from grafana_import.util import read_dashboard_file

MINIMAL_JSON_URL = "https://github.com/grafana-toolbox/grafana-snippets/raw/main/dashboard/native-minimal.json"


@pytest.fixture
def minimal_json_payload() -> str:
    return requests.get(MINIMAL_JSON_URL, timeout=5).text


def test_read_dashboard_json(tmp_path, minimal_json_payload):
    """
    Verify reading a traditional Grafana dashboard in JSON format.
    """
    minimal_json = Path(tmp_path) / "minimal.json"
    minimal_json.write_text(minimal_json_payload)

    dashboard = read_dashboard_file(minimal_json)
    assert dashboard["title"] == "grafana-snippets » Synthetic minimal dashboard"


def test_read_dashboard_python(tmp_path, minimal_json_payload):
    """
    Verify reading a traditional Grafana dashboard in JSON format.
    """
    minimal_json = Path(tmp_path) / "minimal.json"
    minimal_json.write_text(minimal_json_payload)

    dashboard = read_dashboard_file(minimal_json)
    assert dashboard["title"] == "grafana-snippets » Synthetic minimal dashboard"


def test_read_dashboard_unknown(tmp_path):
    """
    A file name without a known suffix will trip the program.
    """
    example_foo = Path(tmp_path) / "example.foo"
    example_foo.touch()

    with pytest.raises(NotImplementedError) as ex:
        read_dashboard_file(example_foo)
    assert ex.match("Decoding file type not implemented, or file is not executable: example.foo")


def test_read_dashboard_builder_file_executable(tmp_path):
    """
    A file name without suffix will automatically be considered a builder, and must be executable.
    """
    builder = Path(tmp_path) / "minimal-builder"
    builder.write_text(f"#!/usr/bin/env sh\ncurl --location {MINIMAL_JSON_URL}")
    builder.chmod(0o777)

    dashboard = read_dashboard_file(builder)
    assert dashboard["title"] == "grafana-snippets » Synthetic minimal dashboard"


def test_read_dashboard_builder_unknown(tmp_path):
    """
    A file of "builder" nature, which is not executable, will trip the program.
    """
    builder = Path(tmp_path) / "unknown-builder"
    builder.touch()

    with pytest.raises(NotImplementedError) as ex:
        read_dashboard_file(builder)
    assert ex.match("Decoding file type not implemented, or file is not executable: unknown-builder")
