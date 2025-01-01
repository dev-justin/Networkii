from setuptools import setup, find_packages

setup(
    name="networkii-cli",
    version="1.0.0",
    packages=find_packages(where="src"),     # Tells setuptools to look in src/
    package_dir={"": "src"},                 # "Root" of packages is src/
    entry_points={
        "console_scripts": [
            "networkii=src.cli:main",        # Use full path to cli.py
        ],
    },
)