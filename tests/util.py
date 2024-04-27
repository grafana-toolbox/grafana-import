import builtins
import io
import json
import typing as t

import pytest
from responses import RequestsMock

if t.TYPE_CHECKING:
    from mypy.typeshed.stdlib._typeshed import FileDescriptorOrPath, OpenTextMode


def mock_grafana_health(responses: RequestsMock) -> None:
    """
    Baseline mock for each Grafana conversation.
    """
    responses.get(
        "http://localhost:3000/api/health",
        json={"database": "ok"},
        status=200,
        content_type="application/json",
    )


def mock_grafana_search(responses: RequestsMock) -> None:
    responses.get(
        "http://localhost:3000/api/search?type=dash-db&limit=5000",
        json=[{"title": "foobar", "uid": "618f7589-7e3d-4399-a585-372df9fa5e85"}],
        status=200,
        content_type="application/json",
    )


def mkdashboard() -> t.Dict[str, t.Any]:
    """
    Example Grafana dashboard, generated using the `grafana-dashboard` package.

    https://github.com/fzyzcjy/grafana_dashboard_python/blob/master/examples/python_to_json/input_python/dashboard-one.py
    """
    pytest.importorskip(
        "grafana_dashboard", reason="Skipping dashboard generation because `grafana-dashboard` is not available"
    )

    from grafana_dashboard.manual_models import TimeSeries
    from grafana_dashboard.model.dashboard_types_gen import Dashboard, GridPos
    from grafana_dashboard.model.prometheusdataquery_types_gen import PrometheusDataQuery

    dashboard = Dashboard(
        title="Dashboard One",
        panels=[
            TimeSeries(
                title="Panel Title",
                gridPos=GridPos(x=0, y=0, w=12, h=9),
                targets=[
                    PrometheusDataQuery(
                        datasource="Prometheus",
                        expr='avg(1 - rate(node_cpu_seconds_total{mode="idle"}[$__rate_interval])) by (instance, job)',
                        legendFormat="{{instance}}",
                    )
                ],
            )
        ],
    ).auto_panel_ids()
    return json.loads(dashboard.to_grafana_json())


# Bookkeeping for `open_write_noop`.
real_open = builtins.open


def open_write_noop(file: "FileDescriptorOrPath", mode: "OpenTextMode" = "r", **kwargs) -> t.IO:
    """
    A replacement for `builtins.open`, masking all write operations.
    """
    if mode and mode.startswith("w"):
        if "b" in mode:
            return io.BytesIO()
        return io.StringIO()
    return real_open(file=file, mode=mode, **kwargs)
