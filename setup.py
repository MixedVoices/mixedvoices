from setuptools import setup, find_packages

setup(
    name="mixedvoices",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'psycopg2-binary>=2.9.9',
        'flask>=2.3.3',
        'requests>=2.31.0',
    ],
)