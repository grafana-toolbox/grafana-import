from importlib.resources import files

import pytest
import responses

from grafana_import.grafana import Grafana
from grafana_import.util import grafana_settings, load_yaml_config
from tests.util import mock_grafana_health, mock_grafana_search


@pytest.fixture(scope="session", autouse=True)
def niquests_patch_all():
    """
    Patch module namespace, pretend Niquests is Requests.
    """
    from sys import modules

    import niquests
    import urllib3

    # Amalgamate the module namespace to make all modules aiming
    # to use `requests`, in fact use `niquests` instead.
    modules["requests"] = niquests
    modules["requests.adapters"] = niquests.adapters
    modules["requests.sessions"] = niquests.sessions
    modules["requests.exceptions"] = niquests.exceptions
    modules["requests.packages.urllib3"] = urllib3


@pytest.fixture
def mocked_responses():
    """
    Provide the `responses` mocking machinery to a pytest environment.
    """
    with responses.RequestsMock() as rsps:
        yield rsps


@pytest.fixture
def mocked_grafana(mocked_responses):
    mock_grafana_health(mocked_responses)
    mock_grafana_search(mocked_responses)


@pytest.fixture
def config():
    config_file = files("grafana_import") / "conf" / "grafana-import.yml"
    return load_yaml_config(str(config_file))


@pytest.fixture
def settings(config):
    return grafana_settings(config, label="default")


@pytest.fixture(autouse=True)
def reset_grafana_importer():
    Grafana.folders = []
    Grafana.dashboards = []


@pytest.fixture
def gio(settings) -> Grafana:
    return Grafana(**settings)
