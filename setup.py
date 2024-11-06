from setuptools import setup, find_packages

setup(
    name="mixedvoices",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "openai-whisper",
        "fastapi>=0.68.0",
        "uvicorn>=0.15.0",
        "python-multipart>=0.0.5",
        "typer>=0.4.0",
        "streamlit>=1.29.0",
        "plotly>=5.18.0",
        "requests>=2.31.0"
    ],
    entry_points={
        "console_scripts": [
            "mixedvoices=mixedvoices.cli:cli",
        ],
    },
    python_requires=">=3.7",
)