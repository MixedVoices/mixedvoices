from setuptools import setup, find_packages

setup(
    name="mixedvoices",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pydantic>=2.5.0",
        "openai>=1.51.0",
        "librosa>=0.10.0",
        "typer>=0.9.0",
        "fastapi>=0.100.0",
        "uvicorn>=0.22.0",
        "python-multipart>=0.0.6",
        "streamlit>=1.28.0",
        "plotly>=5.13.1",
        "streamlit-plotly-events>=0.0.6",
        "networkx>=3.0",
    ],
    entry_points={
        "console_scripts": [
            "mixedvoices=mixedvoices.cli:cli",
        ],
    },
    python_requires=">=3.8",
)