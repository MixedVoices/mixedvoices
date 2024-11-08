import threading
import webbrowser

import typer

from mixedvoices.dashboard.cli import run_dashboard
from mixedvoices import server

cli = typer.Typer()


def run_server_thread(port: int):
    """Run the FastAPI server in a separate thread"""
    server.run_server(port)


@cli.command()
def dashboard(
    server_port: int = typer.Option(8000, help="Port to run the API server on"),
    dash_port: int = typer.Option(8501, help="Port to run the dashboard on"),
):
    """Launch both the MixedVoices API server and dashboard"""
    print(f"Starting MixedVoices API server on http://localhost:{server_port}")
    print(f"Starting MixedVoices dashboard on http://localhost:{dash_port}")

    # Start the FastAPI server in a separate thread
    server_thread = threading.Thread(
        target=run_server_thread, args=(server_port,), daemon=True
    )
    server_thread.start()

    # Open the dashboard in the browser
    webbrowser.open(f"http://localhost:{dash_port}")

    # Run the Streamlit dashboard (this will block)
    run_dashboard(dash_port)


if __name__ == "__main__":
    cli()
