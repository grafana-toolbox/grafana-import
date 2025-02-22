import json
import re
import shlex
import sys
from pathlib import Path
from unittest import mock

import pytest

from grafana_import.cli import main
from tests.util import mkdashboard, open_write_noop

CONFIG_FILE = "grafana_import/conf/grafana-import.yml"


def get_settings_arg(use_settings: bool = True):
    if use_settings:
        return f"--config_file {CONFIG_FILE}"
    return "--grafana_url http://localhost:3000"


def test_no_action_failure(caplog):
    """
    Verify the program fails when invoked without positional `action` argument.
    """
    sys.argv = ["grafana-import"]
    with pytest.raises(SystemExit) as ex:
        main()
    assert ex.match("1")
    assert "Unknown action: None. Use one of: ['import', 'export', 'remove']" in caplog.messages


@pytest.mark.parametrize("use_settings", [True, False], ids=["config-yes", "config-no"])
def test_import_dashboard_success(mocked_grafana, mocked_responses, tmp_path, caplog, use_settings):
    """
    Verify "import dashboard" works.
    """
    mocked_responses.post(
        "http://localhost:3000/api/dashboards/db",
        json={"status": "ok"},
        status=200,
        content_type="application/json",
    )

    dashboard = mkdashboard()
    dashboard_file = Path(tmp_path / "dashboard.json")
    dashboard_file.write_text(json.dumps(dashboard, indent=2))

    sys.argv = shlex.split(f"grafana-import import {get_settings_arg(use_settings)} --dashboard_file {dashboard_file}")

    with pytest.raises(SystemExit) as ex:
        main()
    assert ex.match("0")

    assert "Dashboard 'Dashboard One' imported into folder 'General'" in caplog.messages


@pytest.mark.parametrize("use_settings", [True, False], ids=["config-yes", "config-no"])
def test_export_dashboard_success(mocked_grafana, mocked_responses, caplog, use_settings):
    """
    Verify "export dashboard" works.
    """

    mocked_responses.get(
        "http://localhost:3000/api/dashboards/uid/618f7589-7e3d-4399-a585-372df9fa5e85",
        json={"dashboard": {}},
        status=200,
        content_type="application/json",
    )

    sys.argv = shlex.split(f"grafana-import export {get_settings_arg(use_settings)} --dashboard_name foobar")

    with pytest.raises(SystemExit) as ex:
        m = mock.patch("builtins.open", open_write_noop)
        m.start()
        main()
        m.stop()
    assert ex.match("0")

    assert re.match(r".*OK: Dashboard 'foobar' exported to: ./foobar_\d+.json.*", caplog.text, re.DOTALL)


@pytest.mark.parametrize("use_settings", [True, False], ids=["config-yes", "config-no"])
def test_export_dashboard_notfound(mocked_grafana, mocked_responses, caplog, use_settings):
    """
    Verify "export dashboard" fails appropriately when addressed dashboard does not exist.
    """

    mocked_responses.get(
        "http://localhost:3000/api/dashboards/uid/618f7589-7e3d-4399-a585-372df9fa5e85",
        json={},
        status=404,
        content_type="application/json",
    )

    sys.argv = shlex.split(f"grafana-import export {get_settings_arg(use_settings)} --dashboard_name foobar")
    with pytest.raises(SystemExit) as ex:
        main()
    assert ex.match("1")

    assert "Dashboard name not found: foobar" in caplog.text


@pytest.mark.parametrize("use_settings", [True, False], ids=["config-yes", "config-no"])
def test_remove_dashboard_success(mocked_grafana, mocked_responses, caplog, use_settings):
    """
    Verify "remove dashboard" works.
    """
    mocked_responses.delete(
        "http://localhost:3000/api/dashboards/uid/618f7589-7e3d-4399-a585-372df9fa5e85",
        json={"status": "ok"},
        status=200,
        content_type="application/json",
    )

    sys.argv = shlex.split(f"grafana-import remove {get_settings_arg(use_settings)} --dashboard_name foobar")

    with pytest.raises(SystemExit) as ex:
        main()
    assert ex.match("0")

    assert "OK: Dashboard removed: foobar" in caplog.text
