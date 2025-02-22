"""
## About

Upload a Grafana dashboard file in JSON format to the Grafana server.

## Walkthrough

1. Start Grafana

   docker run --rm -it --publish=3000:3000 --env='GF_SECURITY_ADMIN_PASSWORD=admin' grafana/grafana:11.5.2

2. Import dashboard

   wget https://github.com/simonprickett/mongodb-hotel-jobs/raw/refs/heads/main/grafana_dashboard.json
   python examples/dashboard_import.py grafana_dashboard.json

3. Visit Grafana

   http://admin:admin@localhost:3000/
   Log in using admin:admin.
"""

import json
import sys
from pathlib import Path

from grafana_import.grafana import Grafana


def main():

    # Read single positional CLI argument.
    dashboard_path = Path(sys.argv[1])

    # Load dashboard JSON from filesystem.
    dashboard = json.loads(dashboard_path.read_text())

    # Import dashboard JSON to Grafana.
    # Note: Adjust parameters to match your Grafana.
    #       You can use many variants to authenticate with its API.
    gio = Grafana(url="http://localhost:3000", credential=("admin", "admin"))
    outcome = gio.import_dashboard(dashboard)
    if outcome:
        print("Grafana dashboard imported successfully")
    else:
        print("Grafana dashboard import failed")


if __name__ == "__main__":
    main()
