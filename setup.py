from setuptools import setup, find_namespace_packages

setup(
    name="networkii-cli",
    version="1.0.0",
    package_dir={"": "src"},
    packages=find_namespace_packages(where="src"),
    entry_points={
        "console_scripts": [
            "networkii=cli:main",
        ],
    }
)