import threading
import webbrowser

import typer

from mixedvoices.dashboard.cli import run_dashboard
from mixedvoices.server import server

cli = typer.Typer()


def run_server_thread(port: int):
    """Run the FastAPI server in a separate thread"""
    server.run_server(port)


@cli.command()
def dashboard(
    server_port: int = typer.Option(7760, help="Port to run the API server on"),
    dashboard_port: int = typer.Option(7761, help="Port to run the dashboard on"),
):
    """Launch both the MixedVoices API server and dashboard"""
    print(f"Starting MixedVoices API server on http://localhost:{server_port}")
    print(f"Starting MixedVoices dashboard on http://localhost:{dashboard_port}")

    # Start the FastAPI server in a separate thread
    server_thread = threading.Thread(
        target=run_server_thread, args=(server_port,), daemon=True
    )
    server_thread.start()

    # Open the dashboard in the browser
    webbrowser.open(f"http://localhost:{dashboard_port}")

    # Run the Streamlit dashboard (this will block)
    run_dashboard(dashboard_port)
