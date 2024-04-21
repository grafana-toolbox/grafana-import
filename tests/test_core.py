import pytest

from grafana_import.grafana import Grafana, GrafanaDashboardNotFoundError, GrafanaFolderNotFoundError
from tests.util import mkdashboard, mock_grafana_health


def test_find_dashboard_success(mocked_grafana, gio):
    """
    Verify "find dashboard" works.
    """

    results = gio.find_dashboard("foobar")
    assert results == {"title": "foobar", "uid": "618f7589-7e3d-4399-a585-372df9fa5e85"}


def test_import_dashboard_success(mocked_grafana, mocked_responses, gio):
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
    outcome = gio.import_dashboard(dashboard)
    assert outcome is True


def test_export_dashboard_success(mocked_grafana, mocked_responses, gio):
    """
    Verify "export dashboard" works.
    """
    mocked_responses.get(
        "http://localhost:3000/api/dashboards/uid/618f7589-7e3d-4399-a585-372df9fa5e85",
        json={"dashboard": {}},
        status=200,
        content_type="application/json",
    )

    dashboard = gio.export_dashboard("foobar")
    assert dashboard == {"dashboard": {}}


def test_export_dashboard_notfound(mocked_grafana, mocked_responses, gio):
    """
    Verify "export dashboard" using an unknown dashboard croaks as expected.
    """
    with pytest.raises(GrafanaDashboardNotFoundError) as ex:
        gio.export_dashboard("unknown")
    assert ex.match("Dashboard not found: unknown")


def test_remove_dashboard_success(mocked_grafana, mocked_responses, settings):
    """
    Verify "remove dashboard" works.
    """
    mocked_responses.delete(
        "http://localhost:3000/api/dashboards/uid/618f7589-7e3d-4399-a585-372df9fa5e85",
        json={"status": "ok"},
        status=200,
        content_type="application/json",
    )

    gio = Grafana(**settings)
    outcome = gio.remove_dashboard("foobar")
    assert outcome is True


def test_remove_dashboard_folder_not_found(mocked_responses, settings):
    """
    Verify "remove dashboard" works.
    """

    mock_grafana_health(mocked_responses)

    mocked_responses.get(
        "http://localhost:3000/api/folders",
        json=[],
        status=200,
        content_type="application/json",
    )

    settings["folder"] = "non-standard"
    gio = Grafana(**settings)

    with pytest.raises(GrafanaFolderNotFoundError) as ex:
        gio.remove_dashboard("foobar")

    assert ex.match("Folder not found: non-standard")
