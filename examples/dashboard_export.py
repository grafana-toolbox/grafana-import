"""
## About

Export a Grafana dashboard to a JSON file.

## Walkthrough

1. Start Grafana

   docker run --rm -it --publish=3000:3000 --env='GF_SECURITY_ADMIN_PASSWORD=admin' grafana/grafana:11.5.2

2. Create a dashboard

   Open http://localhost:3000/, log in with admin:admin, and create a dashboard named `my-first-dashboard`.

3. Export dashboard

   python examples/dashboard_export.py my-first-dashboard my-first-dashboard.json
"""

import json
import sys
from pathlib import Path

from grafana_import.grafana import Grafana


def main():

    # Read positional CLI arguments.
    dashboard_name = sys.argv[1]
    output_path = Path(sys.argv[2])

    # Export dashboard JSON from Grafana.
    # Note: Adjust parameters to match your Grafana.
    #       You can use many variants to authenticate with its API.
    gio = Grafana(url="http://localhost:3000", credential=("admin", "admin"))
    dashboard = gio.export_dashboard(dashboard_name)

    # Persist only the dashboard payload, just like Grafana import expects.
    output_path.write_text(json.dumps(dashboard["dashboard"], indent=2, sort_keys=True))

    print(f"Grafana dashboard exported successfully to {output_path}")


if __name__ == "__main__":
    main()
