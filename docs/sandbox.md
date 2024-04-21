# Development Sandbox


## Setup
Those commands will get you started with a sandboxed development environment.
After invoking `poe check`, and observing the software tests succeed, you
should be ready to start hacking.

```shell
git clone https://github.com/peekjef72/grafana-import-tool
cd grafana-import-tool
python3 -m venv .venv
source .venv/bin/activate
pip install --editable='.[develop,test]'
```


## Software tests

For running the software tests after setup, invoke `poe check`.
Optionally, activate the virtualenv, if you are coming back to
development using a fresh terminal session.

Run linters and software tests.
```shell
source .venv/bin/activate
poe check
```

Run a subset of tests.
```shell
pytest -k core 
```


## Releasing

```shell
# Install a few more prerequisites.
pip install --editable='.[release]'

# Designate a new version.
git tag v0.1.0
git push --tags

# Build package, and publish to PyPI.
poe release
```
