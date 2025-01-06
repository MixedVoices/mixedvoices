import contextlib
import sys
from pathlib import Path

import streamlit.web.cli as stcli
import typer

from mixedvoices.dashboard.config import DASHBOARD_PORT


def run_dashboard(port: int = DASHBOARD_PORT):
    """Run the Streamlit dashboard"""
    with contextlib.redirect_stdout(None):
        dashboard_path = Path(__file__).parent / "app.py"
        sys.argv = [
            "streamlit",
            "run",
            str(dashboard_path),
            "--server.port",
            str(port),
            "--server.address",
            "localhost",
        ]
        sys.exit(stcli.main())


def cli():
    """Command line interface function"""
    typer.run(run_dashboard)


if __name__ == "__main__":
    cli()
