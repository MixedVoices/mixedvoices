# mixedvoices/cli.py (updated)
import threading
import webbrowser

import typer

from mixedvoices.config import CONFIG_OPTIONS, DEFAULT_CONFIG, load_config, update_value
from mixedvoices.dashboard.cli import run_dashboard
from mixedvoices.server import server

cli = typer.Typer()


def run_server_thread(port: int):
    """Run the FastAPI server in a separate thread"""
    server.run_server(port)


@cli.command()
def config():
    """Configure model settings interactively"""
    config = load_config()

    for model_name in DEFAULT_CONFIG.keys():
        current_value = config.get(model_name, DEFAULT_CONFIG[model_name])
        print(f"\nCurrent value for {model_name}: {current_value}")

        # Show available options if they exist for this field
        prompt_text = "Enter new value (or press Enter to keep current)"
        if model_name in CONFIG_OPTIONS:
            options_str = ", ".join(CONFIG_OPTIONS[model_name])
            prompt_text = f"Options: {options_str}\n{prompt_text}"

        while True:
            new_value = typer.prompt(
                prompt_text, default=current_value, show_default=False
            )
            if new_value == current_value:
                print("Keeping current value...")
                break

            try:
                update_value(model_name, new_value)
                print(f"Updated {model_name} to: {new_value}")
                break
            except ValueError as e:
                print(f"Error: {str(e)}")
                if not typer.confirm("Try again?", default=True):
                    print("Keeping current value...")
                    break


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
