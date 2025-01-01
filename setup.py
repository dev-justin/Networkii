from setuptools import setup, find_packages

setup(
    name="networkii-cli",
    version="1.0.0",
    packages=find_packages(where="src"),
    package_dir={"networkii": "src"},
    entry_points={
        "console_scripts": [
            "networkii=networkii.cli:main",
        ],
    },
)