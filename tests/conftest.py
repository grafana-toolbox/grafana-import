import os
import sys
import typing as t

import pytest
import responses

from grafana_import.grafana import Grafana
from grafana_import.util import grafana_settings, load_yaml_config
from tests.util import mock_grafana_health, mock_grafana_search

if sys.version_info < (3, 9):
    from importlib_resources import files
else:
    from importlib.resources import files


@pytest.fixture(scope="session", autouse=True)
def niquests_patch_all():
    """
    Patch module namespace, pretend Niquests is Requests.
    """
    from sys import modules

    try:
        import niquests
    except ImportError:
        return
    import urllib3

    # Amalgamate the module namespace to make all modules aiming
    # to use `requests`, in fact use `niquests` instead.
    modules["requests"] = niquests
    modules["requests.adapters"] = niquests.adapters
    modules["requests.sessions"] = niquests.sessions
    modules["requests.exceptions"] = niquests.exceptions
    modules["requests.packages.urllib3"] = urllib3


@pytest.fixture(scope="session", autouse=True)
def reset_environment():
    """
    Make sure relevant environment variables do not leak into the test suite.
    """
    if "GRAFANA_URL" in os.environ:
        del os.environ["GRAFANA_URL"]


@pytest.fixture
def mocked_responses():
    """
    Provide the `responses` mocking machinery to a pytest environment.
    """
    if sys.version_info < (3, 7):
        raise pytest.skip("Does not work on Python 3.6")
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
    return grafana_settings(url=None, config=config, label="default")


@pytest.fixture(autouse=True)
def reset_grafana_importer():
    Grafana.folders = []
    Grafana.dashboards = []


@pytest.fixture
def gio_factory(settings) -> t.Callable:
    def mkgrafana(use_settings: bool = True) -> Grafana:
        if use_settings:
            return Grafana(**settings)
        return Grafana(url="http://localhost:3000")

    return mkgrafana
